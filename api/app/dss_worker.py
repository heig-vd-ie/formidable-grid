from datetime import datetime, timedelta
import json
import os
import random
import time

import numpy as np
import pandas as pd
import psutil
import ray
from tqdm import tqdm

from extract_data.profile_reader import ProfileData, ProfileReader
from app.helpers import setup_circuit
from app.models import SimulationResponse
from common.konfig import (
    H_SYSTEM,
    MAX_CPU_COUNT,
    MAX_ITERATION,
    NOMINAL_FREQUENCY,
    NOMINAL_POWER,
    OUTPUT_FOLDER,
    SMALL_NUMBER,
)
from common.setup_log import setup_logger
from pathlib import Path

logger = setup_logger(__name__)

SERVER_RAY_ADDRESS = os.getenv("SERVER_RAY_ADDRESS", None)


def ray_init():
    logger.info(f"Initializing Ray with address: {SERVER_RAY_ADDRESS}")
    return ray.init(
        address=SERVER_RAY_ADDRESS,
        runtime_env={
            "working_dir": str(Path(__file__).parent.parent.resolve()),
        },
    )


def ray_shutdown():
    ray.shutdown()


@ray.remote
class DSSWorker:
    def __init__(
        self,
        basedir: str,
        temp_file: str,
        env_vars: dict,
        profiles: ProfileData,
        **kwargs,
    ):
        from opendssdirect import dss

        self.basedir = basedir
        self.temp_file = temp_file
        self.dss = dss
        self.profiles = profiles
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        self.__init_dir(env_vars)
        self._initialize_circuit(temp_file)
        self.buses = self.dss.Circuit.AllBusNames() or []
        self._add_extra_units(**kwargs)
        self.__init_components()

    def __init_dir(self, env_vars: dict):
        for key, value in env_vars.items():
            os.environ[key] = value
        os.chdir(self.basedir)

    def __init_components(self):
        """Initialize component lists from the OpenDSS circuit"""
        self.loads = self.dss.Loads.AllNames() or []
        self.lines = self.dss.Lines.AllNames() or []
        self.transformers = self.dss.Transformers.AllNames() or []
        self.generators = self.dss.Generators.AllNames() or []
        self.storages = self.dss.Storages.AllNames() or []
        self.pvsystems = self.dss.PVsystems.AllNames() or []

        self.loadshapes = [
            l for l in self.dss.LoadShape.AllNames() or [] if not "pvshape" in l
        ]
        self.pvloadshapes = [
            l for l in self.dss.LoadShape.AllNames() or [] if "pvshape" in l
        ]
        self.vsources = self.dss.Vsources.AllNames() or []

    def _initialize_circuit(self, temp_file: str):
        """Initialize the OpenDSS circuit from the given .dss file"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{temp_file}"')

    def _change_seed(self, seed_number: int | None):
        """Change the random seed for reproducibility"""
        random.seed(seed_number)
        np.random.seed(seed_number)

    def _add_extra_units(
        self,
        number_of_pvs: int = 5,
        pv_capacity_kva_mean: float = 10.0,
        storage_capacity_kw_mean: float = 20.0,
        grid_forming_percent: float = 0.5,
        seed_number: int = 42,
    ):
        """Add extra PV systems and storage units to the circuit for testing"""
        self.gfm_inv = []
        for i in range(number_of_pvs):
            self._change_seed(seed_number + i)
            bus_name = random.choice(self.buses)
            pv_capacity_kva = max([0, pv_capacity_kva_mean * random.uniform(0.5, 1.5)])
            storage_capacity_kva = max(
                [0, storage_capacity_kw_mean * random.uniform(0.5, 1.5)]
            )
            storage_capacity_kwh = storage_capacity_kva * 4.0
            pv_shape = "pvshape" + str((i % 5) + 1)  # Cycle through pvshape1-5
            self.dss.Command(
                self._add_pv_systems(i, bus_name, pv_capacity_kva, pv_shape)
            )
            self.dss.Command(
                self._add_storage_units(
                    i, bus_name, storage_capacity_kva, storage_capacity_kwh
                )
            )
            if random.random() < grid_forming_percent:  # is it grid-forming?
                self.gfm_inv.append(i)

        self.__init_components()

    def _add_pv_systems(
        self,
        i: int,
        bus_name: str,
        pv_capacity_kva: float,
        pv_shape: str,
    ):
        return f'New "PVSystem.PV{i+1}" Phases=3 conn=delta Bus1={bus_name} kV=0.48 pmpp=100 daily={pv_shape} kVA={pv_capacity_kva} %X=50 kP=0.3 KVDC=0.700 PITol=0.1'

    def _add_storage_units(
        self,
        i: int,
        bus_name: str,
        storage_capacity_kva: float,
        storage_capacity_kwh: float,
    ):
        return f'New "Storage.Storage{i+1}" Phases=3 conn=delta Bus1={bus_name} kV=0.48 kva={storage_capacity_kva} kWrated={storage_capacity_kva} kWhrated={storage_capacity_kwh} %stored=100 %reserve=20 '

    def _set_load_shape_multipliers(self, curr_datetime: datetime):
        """Randomly set load shape multipliers for all load shapes"""
        pv = self.profiles.pv[self.profiles.pv.index == curr_datetime]
        load_p = self.profiles.load_p[self.profiles.load_p.index == curr_datetime]
        load_q = self.profiles.load_q[self.profiles.load_q.index == curr_datetime]
        if pv.empty or load_p.empty or load_q.empty:
            logger.warning(f"No profile data found for {curr_datetime}")
            return
        for i in range(len(self.loadshapes)):
            col_name = load_p.columns[i % len(load_p.columns)]
            multiplier = load_p.iloc[0][col_name]
            self.dss.run_command(
                f"Edit LoadShape.{self.loadshapes[i]} npts=1 mult=[{multiplier}]"
            )
        for i in range(len(self.pvloadshapes)):
            col_name = pv.columns[i % len(pv.columns)]
            multiplier = pv.iloc[0][col_name]
            self.dss.run_command(
                f"Edit LoadShape.{self.pvloadshapes[i]} npts=1 mult=[{multiplier}]"
            )
        # TODO: Set multiplier of reactive power based on load_q profile

    def _solve(self, curr_datetime: datetime):
        """Run power flow analysis for a single timestep"""
        time_start = time.time()
        self._set_load_shape_multipliers(curr_datetime)
        self.dss.run_command("Solve")
        freq = self._update_freq(NOMINAL_FREQUENCY)
        for _ in range(MAX_ITERATION):
            self.dss.run_command("Solve")
            new_freq = self._update_freq(freq)
            if abs(new_freq - freq) / NOMINAL_FREQUENCY < SMALL_NUMBER:
                break
            freq = new_freq
        time_end = time.time()
        return time_end - time_start, freq

    def _update_freq(self, freq: float):
        """Update the system frequency in the OpenDSS simulation"""
        Δp = 0.0
        Δq = 0.0
        for vsource in self.vsources:
            self.dss.Circuit.SetActiveElement(f"Vsource.{vsource}")
            Δp += self.dss.CktElement.Powers()[0]
            Δq += self.dss.CktElement.Powers()[1]

        freq -= Δp / (2 * H_SYSTEM * NOMINAL_POWER)

        self.dss.run_command(f"Edit Vsource.V1 basefreq={freq}")
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            power = self.dss.CktElement.Powers()
            new_p_kw = power[0] + Δp * 0.1
            new_q_kvar = power[1] + Δq * 0.1
            self.dss.run_command(
                f"Edit Storage.{storage} kW={new_p_kw:.2f} kvar={new_q_kvar:.2f}"
            )
        for pv in self.pvsystems:
            self.dss.Circuit.SetActiveElement(f"PVSystem.{pv}")
            power = self.dss.CktElement.Powers()
            new_q_kvar = power[1] + Δq * 0.1
            self.dss.run_command(f"Edit PVSystem.{pv} kvar={new_q_kvar:.2f}")
        return freq

    def _get_dict_data(self, klass: str) -> dict:
        """Get all data for a given class as a dictionary"""
        elements = self.__getattribute__(f"{klass}s")
        results = {}
        for element in elements:
            self.dss.Circuit.SetActiveElement(f"{klass}.{element}")
            results[f"{klass}.{element}"] = {
                "bus_names": self.dss.CktElement.BusNames(),
                "powers": self.dss.CktElement.Powers(),
                "voltages": self.dss.CktElement.Voltages(),
                "currents": self.dss.CktElement.Currents(),
            }
        return results

    def _get_voltages(self) -> dict:
        """Get voltages at all buses"""
        voltages_dict = {}
        for bus in self.buses:
            self.dss.Circuit.SetActiveBus(bus)
            voltages_dict[bus] = self.dss.Bus.Voltages()

        return voltages_dict

    def dump_results(self, delta_time: float, curr_datetime: datetime, freq: float):
        """Dump results to a JSON file for the current timestep"""
        timestamp = curr_datetime.strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": curr_datetime.isoformat(),
            "solve_time_ms": delta_time,
            "converged": True if self.dss.Solution.Converged() else False,
            "frequency": freq,
            "losses": self.dss.Circuit.Losses(),
            "voltages": self._get_voltages(),
            "lines": self._get_dict_data("line"),
            "loads": self._get_dict_data("load"),
            "generators": self._get_dict_data("generator"),
            "storages": self._get_dict_data("storage"),
            "pvsystems": self._get_dict_data("pvsystem"),
            "vsources": self._get_dict_data("vsource"),
        }
        output_path = os.path.join(OUTPUT_FOLDER, f"results_{timestamp}.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=4)

    def solve(self, curr_datetime: datetime):
        """Run power flow and extract results"""
        delta_time, freq = self._solve(curr_datetime)
        self.dump_results(delta_time, curr_datetime, freq=freq)


def run_daily_powerflow(
    dss_filename: str = "Run_QSTS.dss",
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
    **kwargs,
):
    """
    Run power flow analysis for each hour of a day using Ray for parallel execution
    """
    cpu_count = psutil.cpu_count() or MAX_CPU_COUNT
    logger.info(f"System has {cpu_count} CPU cores available")

    if not ray.is_initialized():
        ray_init()
        logger.info("Ray was not initialized, initializing now...")
    else:
        logger.info("Ray is already initialized")

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    profiles = ProfileReader().process_and_record_profiles().get_profiles()

    total_runs = int((to_datetime - from_datetime).total_seconds() // (60 * 15))
    run_indices = list(range(total_runs))
    logger.info(f"Total runs: {total_runs}")

    workers = [
        DSSWorker.remote(basedir, temp_file, env_vars, profiles, **kwargs)
        for _ in range(cpu_count - 1)
    ]

    # Dynamic task assignment: assign new run_idx to a worker as soon as it is free
    futures = []
    run_iter = iter(run_indices)

    # Start one task per worker
    for worker in workers:
        try:
            run_idx = next(run_iter)
            futures.append(
                (
                    worker,
                    worker.solve.remote(
                        from_datetime + timedelta(minutes=run_idx * 15),
                    ),
                )
            )
        except StopIteration:
            break

    pbar = tqdm(total=total_runs, desc="Running Power Flows")
    while futures:
        # Wait for any future to complete
        done_ids, _ = ray.wait([f[1] for f in futures])
        done_id = done_ids[0]
        # Find which worker finished
        for i, (worker, future) in enumerate(futures):
            if future == done_id:
                try:
                    ray.get(done_id)
                except Exception as _:
                    logger.error(f"Error in worker id {done_id}, skipping this run...")
                    ray.cancel(done_id)
                pbar.update(1)
                # Assign new task to this worker if any left
                try:
                    run_idx = next(run_iter)
                    new_future = worker.solve.remote(
                        from_datetime + timedelta(minutes=run_idx * 15)
                    )
                    futures[i] = (worker, new_future)
                except StopIteration:
                    # No more tasks, remove this worker from the list
                    futures.pop(i)
                break
    pbar.close()
    os.remove(temp_file)


def read_results():
    """Read all JSON result files and return as a list of dictionaries"""
    results = []
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith(".json"):
            with open(os.path.join(OUTPUT_FOLDER, file), "r") as f:
                data = json.load(f)
                results.append(data)
    return _save_and_summarize_results(results)


def _save_and_summarize_results(results: list[SimulationResponse]) -> pd.DataFrame:
    """Save results to CSV and print summary statistics"""
    # Convert to DataFrame
    df = pd.DataFrame(
        [r.__dict__ if hasattr(r, "__dict__") else dict(r) for r in results]
    )
    # Sort by datetime to ensure proper order
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Performance summary
    avg_solve_time = df["solve_time_ms"].mean()
    logger.info(f"Average OpenDSS solve time: {avg_solve_time:.2f} ms")
    logger.info(f"Speedup achieved through parallelization!")
    ray_shutdown()
    return df
