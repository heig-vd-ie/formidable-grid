import os
import time
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime, timedelta
from plotter import create_qsts_plots
from helpers import setup_circuit
import ray
import psutil
from profile_reader import load_pv_profile


@ray.remote
def run_powerflow_timestep(temp_file, run_index, base_dir, env_vars, pv_multiplier):
    """Run power flow analysis for a single timestep"""
    # Import OpenDSS inside the remote function to avoid serialization issues
    from opendssdirect import dss

    # Set environment variables in the worker
    for key, value in env_vars.items():
        os.environ[key] = value

    # Change to the correct working directory
    os.chdir(base_dir)

    current_hour = run_index // 60
    current_minute = (run_index % 60) * 1
    current_second = 0

    # Load PV profile multipliers
    dss.Command("Clear")
    dss.Command(f'Compile "{temp_file}"')
    dss.run_command(f"Edit LoadShape.pvshape npts=1 mult=[{pv_multiplier}]")
    solve_time = time.time()
    dss.run_command("Solve")
    solve_time = time.time() - solve_time
    converged = dss.Solution.Converged()

    if converged:
        total_power = dss.Circuit.TotalPower()
        losses = dss.Circuit.Losses()

        # Get bus voltages
        key_buses = [
            "101",
            "108",
            "610",
        ]
        bus_voltages = {}
        for bus in key_buses:
            dss.Circuit.SetActiveBus(bus)
            voltages = dss.Bus.Voltages()
            voltage_mag = (
                np.sqrt(voltages[0] ** 2 + voltages[1] ** 2)
                if len(voltages) >= 2
                else 0
            )
            bus_voltages[f"V_{bus}"] = voltage_mag

        # Get PV and Storage data
        dss.Circuit.SetActiveElement("PVSystem.myPV")
        pv_power = dss.CktElement.Powers()
        pv_real_power = pv_power[0] if pv_power else 0
        pv_reactive_power = pv_power[1] if len(pv_power) > 1 else 0

        dss.Circuit.SetActiveElement("Storage.mystorage")
        storage_power = dss.CktElement.Powers()
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
        + timedelta(hours=current_hour, minutes=current_minute, seconds=current_second),
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


def to_iterator(obj_ids):
    while obj_ids:
        done, obj_ids = ray.wait(obj_ids)
        yield ray.get(done[0])


def run_daily_powerflow(total_runs=24 * 60):
    """Run power flow analysis for each hour of a day using Ray for parallel execution"""

    # Get system info
    cpu_count = psutil.cpu_count()
    print(f"System has {cpu_count} CPU cores available")

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

    # Submit all tasks to Ray
    futures = [
        run_powerflow_timestep.remote(
            temp_file, run_idx, base_dir, env_vars, pv_multipliers[run_idx]
        )
        for run_idx in run_indices
    ]

    results = []
    for x in tqdm(to_iterator(futures), total=len(futures)):
        results.append(x)

    os.remove(temp_file)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Sort by datetime to ensure proper order
    df = df.sort_values("datetime").reset_index(drop=True)

    csv_path = os.path.join(
        os.getenv("DSS_EXPORT_FOLDER", ""), "daily_powerflow_hourly_results.csv"
    )
    df.to_csv(csv_path, index=False)
    print(f"Results saved to: {csv_path}")

    # Check convergence
    converged_count = df["converged"].sum()
    print(
        f"Convergence rate: {converged_count}/{total_runs} ({100*converged_count/total_runs:.1f}%)"
    )

    # Performance summary
    avg_solve_time = df["solve_time_ms"].mean()
    print(f"Average OpenDSS solve time: {avg_solve_time:.2f} ms")
    print(f"Speedup achieved through parallelization!")

    return df, create_qsts_plots


if __name__ == "__main__":
    df, create_qsts_plots = run_daily_powerflow()
    create_qsts_plots(df)
    if ray.is_initialized():
        ray.shutdown()
        print("Ray shutdown complete.")
