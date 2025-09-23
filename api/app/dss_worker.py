from datetime import datetime, timedelta
import json
import os
import random
import time

from main import RayInit, RayShutdown
import numpy as np
import pandas as pd
import psutil
import ray
from tqdm import tqdm

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

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(self, basedir: str, temp_file: str, env_vars: dict):
        from opendssdirect import dss

        self.basedir = basedir
        self.temp_file = temp_file
        self.dss = dss
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        self.__init_dir(env_vars)
        self._initialize_circuit(temp_file)
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
        self.buses = self.dss.Circuit.AllBusNames() or []
        self.loadshapes = self.dss.LoadShape.AllNames() or []
        self.vsources = self.dss.Vsources.AllNames() or []

    def _initialize_circuit(self, temp_file: str):
        """Initialize the OpenDSS circuit from the given .dss file"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{temp_file}"')

    def _set_load_shape_multipliers(self):
        """Randomly set load shape multipliers for all load shapes"""
        # TODO: Replace with actual profile data
        for i in range(len(self.loadshapes)):
            multiplier = random.uniform(0.0, 1.0)
            self.dss.run_command(
                f"Edit LoadShape.{self.loadshapes[i]} npts=1 mult=[{multiplier}]"
            )

    def _solve(self):
        """Run power flow analysis for a single timestep"""
        time_start = time.time()
        self._set_load_shape_multipliers()
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
        delta_time, freq = self._solve()
        self.dump_results(delta_time, curr_datetime, freq=freq)


def run_daily_powerflow(dss_filename: str = "Run_QSTS.dss", total_runs: int = 24 * 1):
    """
    Run power flow analysis for each hour of a day using Ray for parallel execution
    """
    cpu_count = psutil.cpu_count() or MAX_CPU_COUNT
    logger.info(f"System has {cpu_count} CPU cores available")

    RayInit().get()  # Ensure Ray is initialized

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    # pv_multipliers = load_pv_profile()

    run_indices = list(range(total_runs))

    workers = [
        DSSWorker.remote(basedir, temp_file, env_vars) for _ in range(cpu_count - 1)
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
                        datetime(2024, 1, 1) + timedelta(hours=run_idx),
                    ),
                )
            )
        except StopIteration:
            break

    pbar = tqdm(total=len(run_indices))
    while futures:
        # Wait for any future to complete
        done_ids, _ = ray.wait([f[1] for f in futures])
        done_id = done_ids[0]
        # Find which worker finished
        for i, (worker, future) in enumerate(futures):
            if future == done_id:
                ray.get(done_id)
                pbar.update(1)
                # Assign new task to this worker if any left
                try:
                    run_idx = next(run_iter)
                    new_future = worker.solve.remote(run_idx)
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
    RayShutdown().get()  # Shutdown Ray
    return df
