from datetime import datetime, timedelta
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
from app.models import PowerFlow, SimulationResult, tuple_to_powerflow

# from app.profile_reader import load_pv_profile
from common.konfig import LOCAL_MODE, MAX_CPU_COUNT, MAX_ITERATION, SMALL_NUMBER
from common.setup_log import setup_logger

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(self, basedir: str, temp_file: str, env_vars: dict):
        from opendssdirect import dss

        self.basedir = basedir
        self.temp_file = temp_file
        self.dss = dss
        self.__init_dir(env_vars)
        self._initialize_circuit(temp_file)
        self.__init_components()

    def __init_dir(self, env_vars: dict):
        for key, value in env_vars.items():
            os.environ[key] = value
        os.chdir(self.basedir)

    def __init_components(self):
        """Initialize component lists from the OpenDSS circuit"""
        self.loads = self.dss.Loads.AllNames()
        self.generators = self.dss.Generators.AllNames()
        self.storages = self.dss.Storages.AllNames()
        self.pvsystems = self.dss.PVsystems.AllNames()
        self.buses = self.dss.Circuit.AllBusNames()
        self.loadshapes = self.dss.LoadShape.AllNames()

    def _initialize_circuit(self, temp_file: str):
        """Initialize the OpenDSS circuit from the given .dss file"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{temp_file}"')

    def _set_load_shape_multipliers(self):
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
        freq = self._update_freq(50.0)
        for _ in range(MAX_ITERATION):
            self.dss.run_command("Solve")
            new_freq = self._update_freq(freq)
            if abs(new_freq - freq) < SMALL_NUMBER:
                break
            freq = new_freq
        time_end = time.time()
        return time_end - time_start, freq

    def _update_freq(self, freq: float):
        """Update the system frequency in the OpenDSS simulation"""
        self.dss.Circuit.SetActiveElement("Vsource.V1")
        p_kw = self.dss.CktElement.Powers()[0]  # list: [P1,Q1, P2,Q2, ...]
        q_kvar = self.dss.CktElement.Powers()[1]
        Δp = p_kw
        Δq = q_kvar
        freq -= Δp * 0.0001
        self.dss.run_command(f"Edit Vsource.V1 basefreq={freq}")
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            power = self.dss.CktElement.Powers()
            p_kw = power[0]
            q_kvar = power[1]
            new_p_kw = p_kw + Δp * 0.1
            new_q_kvar = q_kvar + Δq * 0.1
            self.dss.run_command(
                f"Edit Storage.{storage} kW={new_p_kw:.2f} kvar={new_q_kvar:.2f}"
            )
        for pv in self.pvsystems:
            self.dss.Circuit.SetActiveElement(f"PVSystem.{pv}")
            power = self.dss.CktElement.Powers()
            p_kw = power[0]
            q_kvar = power[1]
            new_p_kw = p_kw
            new_q_kvar = q_kvar + Δq * 0.1
            self.dss.run_command(f"Edit PVSystem.{pv} kvar={new_q_kvar:.2f}")
        return freq

    def get_results(
        self,
        delta_time: float,
        curr_datetime: datetime,
        key_buses: list[str] | None = None,
        key_storages: list[str] | None = None,
        key_pvs: list[str] | None = None,
        freq: float = 50.0,
    ) -> SimulationResult:
        """Extract results from the OpenDSS simulation"""
        if key_buses is None:
            key_buses = ["101", "108", "610"]
        if key_pvs is None:
            key_pvs = ["PVSystem.myPV"]
        if key_storages is None:
            key_storages = ["Storage.mystorage"]

        converged = self.dss.Solution.Converged()
        if converged:
            total_power = tuple_to_powerflow(self.dss.Circuit.TotalPower())
            losses = tuple_to_powerflow(self.dss.Circuit.Losses())

            bus_voltages = {}
            for bus in key_buses:
                self.dss.Circuit.SetActiveBus(bus)
                voltages = self.dss.Bus.Voltages()
                voltage_mag = (
                    np.sqrt(voltages[0] ** 2 + voltages[1] ** 2)
                    if len(voltages) >= 2
                    else 0
                )
                bus_voltages[bus] = voltage_mag

            # Get PV and Storage data
            pv_powers = {}
            for pv in key_pvs:
                self.dss.Circuit.SetActiveElement(pv)
                pv_power = tuple_to_powerflow(self.dss.CktElement.Powers())
                pv_powers[pv] = pv_power

            storage_powers = {}
            for storage in key_storages:
                self.dss.Circuit.SetActiveElement(storage)
                storage_power = tuple_to_powerflow(self.dss.CktElement.Powers())
                storage_powers[storage] = storage_power
        else:
            logger.warning("Power flow did not converge")
            total_power = PowerFlow()
            losses = PowerFlow()
            bus_voltages = {bus: float("nan") for bus in key_buses}
            pv_powers = {pv: PowerFlow() for pv in key_pvs}
            storage_powers = {storage: PowerFlow() for storage in key_storages}
        return SimulationResult(
            curr_datetime=curr_datetime.isoformat(),
            converged=True if converged else False,
            solve_time_ms=delta_time,
            total_power=total_power,
            losses=losses,
            bus_voltages=bus_voltages,
            pv_powers=pv_powers,
            storage_powers=storage_powers,
            frequency=freq,
        )

    def solve(
        self,
        curr_datetime: datetime,
    ) -> SimulationResult:
        """Run power flow and extract results"""
        delta_time, freq = self._solve()
        result = self.get_results(delta_time, curr_datetime, freq=freq)
        return result


def run_daily_powerflow(
    dss_filename: str = "Run_QSTS.dss",
    total_runs: int = 24 * 1,
) -> pd.DataFrame:
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
    results = []
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
                result = ray.get(done_id)
                results.append(result)
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

    # Convert to DataFrame
    df = pd.DataFrame(
        [r.__dict__ if hasattr(r, "__dict__") else dict(r) for r in results]
    )

    # Sort by datetime to ensure proper order
    df = df.sort_values("curr_datetime").reset_index(drop=True)

    csv_path = os.path.join(
        env_vars["DSS_EXPORT_FOLDER"], "daily_powerflow_hourly_results.csv"
    )
    df.to_csv(csv_path, index=False)
    logger.info(f"Results saved to: {csv_path}")

    # Check convergence
    converged_count = df["converged"].sum()
    logger.info(
        f"Convergence rate: {converged_count}/{total_runs} ({100*converged_count/total_runs:.1f}%)"
    )

    # Performance summary
    avg_solve_time = df["solve_time_ms"].mean()
    logger.info(f"Average OpenDSS solve time: {avg_solve_time:.2f} ms")
    logger.info(f"Speedup achieved through parallelization!")

    RayShutdown().get()  # Shutdown Ray
    return df
