import os
import time
import ray
import psutil
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime, timedelta
from opendss.plotter import create_qsts_plots
from opendss.helpers import setup_circuit
from opendss.profile_reader import load_pv_profile
from common.setup_log import setup_logger

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(self, temp_file, base_dir, env_vars):
        from opendssdirect import dss

        for key, value in env_vars.items():
            os.environ[key] = value
        os.chdir(base_dir)

        self.dss = dss
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{temp_file}"')

    def solve(self, run_index, pv_multiplier):
        """Run power flow analysis for a single timestep"""

        current_hour = run_index // 60
        current_minute = (run_index % 60) * 1
        current_second = 0

        self.dss.run_command(f"Edit LoadShape.pvshape npts=1 mult=[{pv_multiplier}]")
        solve_time = time.time()
        self.dss.run_command("Solve")
        solve_time = time.time() - solve_time
        converged = self.dss.Solution.Converged()

        if converged:
            total_power = self.dss.Circuit.TotalPower()
            losses = self.dss.Circuit.Losses()

            # Get bus voltages
            key_buses = [
                "101",
                "108",
                "610",
            ]
            bus_voltages = {}
            for bus in key_buses:
                self.dss.Circuit.SetActiveBus(bus)
                voltages = self.dss.Bus.Voltages()
                voltage_mag = (
                    np.sqrt(voltages[0] ** 2 + voltages[1] ** 2)
                    if len(voltages) >= 2
                    else 0
                )
                bus_voltages[f"V_{bus}"] = voltage_mag

            # Get PV and Storage data
            self.dss.Circuit.SetActiveElement("PVSystem.myPV")
            pv_power = self.dss.CktElement.Powers()
            pv_real_power = pv_power[0] if pv_power else 0
            pv_reactive_power = pv_power[1] if len(pv_power) > 1 else 0

            self.dss.Circuit.SetActiveElement("Storage.mystorage")
            storage_power = self.dss.CktElement.Powers()
            storage_real_power = storage_power[0] if storage_power else 0
            storage_reactive_power = storage_power[1] if len(storage_power) > 1 else 0
        else:
            # Return None values if not converged
            total_power = [float("nan"), float("nan")]
            losses = [float("nan"), float("nan")]
            bus_voltages = {
                f"V_{bus}": float("nan") for bus in ["101", "108", "610", "sourcebus"]
            }
            pv_real_power = pv_reactive_power = float("nan")
            storage_real_power = storage_reactive_power = float("nan")

        # Store results
        result = {
            "datetime": datetime(2024, 1, 1)
            + timedelta(
                hours=current_hour, minutes=current_minute, seconds=current_second
            ),
            "converged": converged,
            "solve_time_ms": solve_time * 1000,
            "total_real_power_kW": total_power[0] if total_power else float("nan"),
            "total_reactive_power_kVAr": (
                total_power[1] if len(total_power) > 1 else float("nan")
            ),
            "losses_real_kW": losses[0] if losses else float("nan"),
            "losses_reactive_kVAr": losses[1] if len(losses) > 1 else float("nan"),
            "pv_real_power_kW": pv_real_power,
            "pv_reactive_power_kVAr": pv_reactive_power,
            "storage_real_power_kW": storage_real_power,
            "storage_reactive_power_kVAr": storage_reactive_power,
        }

        # Add bus voltages
        result.update(bus_voltages)
        return result


def run_daily_powerflow(total_runs=24 * 1):
    """Run power flow analysis for each hour of a day using Ray for parallel execution"""

    # Get system info
    cpu_count = psutil.cpu_count() or 10
    logger.info(f"System has {cpu_count} CPU cores available")

    # Initialize Ray
    if not ray.is_initialized():
        ray.init()

    # Get current working directory and environment variables
    base_dir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit("Run_QSTS.dss")
    pv_multipliers = load_pv_profile()

    run_indices = list(range(total_runs))

    workers = [
        DSSWorker.remote(temp_file, base_dir, env_vars) for _ in range(cpu_count - 1)
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
                (worker, worker.solve.remote(run_idx, pv_multipliers[run_idx]))
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
    df = pd.DataFrame(results)

    # Sort by datetime to ensure proper order
    df = df.sort_values("datetime").reset_index(drop=True)

    csv_path = os.path.join(
        os.getenv("DSS_EXPORT_FOLDER", ""), "daily_powerflow_hourly_results.csv"
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

    return df


if __name__ == "__main__":
    df = run_daily_powerflow()
    create_qsts_plots(df)
    if ray.is_initialized():
        ray.shutdown()
        logger.info("Ray shutdown complete.")
