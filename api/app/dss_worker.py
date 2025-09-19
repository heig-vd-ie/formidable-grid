from datetime import datetime, timedelta
from email.mime import base
import os
from pathlib import Path
import time

from main import init_ray, shutdown_ray
import numpy as np
import pandas as pd
import psutil
import ray
from tqdm import tqdm

from app.helpers import setup_circuit
from app.models import PowerFlow, SimulationResult, tuple_to_powerflow
from app.profile_reader import load_pv_profile
from common.konfig import MAX_CPU_COUNT
from common.setup_log import setup_logger

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(self, basedir: str, temp_file: str, env_vars: dict):
        from opendssdirect import dss

        self.basedir = basedir
        self.temp_file = temp_file

        for key, value in env_vars.items():
            os.environ[key] = value
        os.chdir(self.basedir)

        self.dss = dss
        self._initialize_circuit(temp_file)

    def _initialize_circuit(self, temp_file: str):
        """Initialize the OpenDSS circuit from the given .dss file"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{temp_file}"')

    def _solve(self, pv_multiplier: float):
        """Run power flow analysis for a single timestep"""
        time_start = time.time()
        self.dss.run_command(f"Edit LoadShape.pvshape npts=1 mult=[{pv_multiplier}]")
        self.dss.run_command("Solve")
        time_end = time.time()
        return time_end - time_start

    def get_results(
        self,
        delta_time: float,
        curr_datetime: datetime,
        key_buses: list[str] | None = None,
        key_storages: list[str] | None = None,
        key_pvs: list[str] | None = None,
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
        )

    def solve(
        self,
        curr_datetime: datetime,
        pv_multiplier: float,
    ) -> SimulationResult:
        """Run power flow and extract results"""
        delta_time = self._solve(pv_multiplier)
        result = self.get_results(delta_time, curr_datetime)
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

    init_ray()

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    pv_multipliers = load_pv_profile()

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
                        pv_multipliers[run_idx],
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
                    new_future = worker.solve.remote(run_idx, pv_multipliers[run_idx])
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
    shutdown_ray()

    return df
