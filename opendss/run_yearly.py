import os
import time
import pandas as pd
from tqdm import tqdm
import numpy as np
from opendssdirect import dss
from datetime import datetime, timedelta
from helpers import setup_circuit
from plotter import create_qsts_plots


def run_daily_powerflow():
    """Run power flow analysis for each hour of a day"""
    print("Starting daily power flow analysis...")
    setup_circuit("Run_QSTS.dss")

    # Data storage
    results = []
    total_runs = 24 * 6
    for run in tqdm(range(total_runs), desc="Simulating ...", unit="run"):
        current_hour = run // 6
        current_minute = (run % 6) * 10
        current_second = 0

        # Set time in OpenDSS (hour, second_of_hour)
        dss.run_command(f"Set time=({current_hour},0)")

        solve_time = time.time()
        dss.run_command("Solve")
        solve_time = time.time() - solve_time
        converged = dss.Solution.Converged()

        if converged:
            total_power = dss.Circuit.TotalPower()
            losses = dss.Circuit.Losses()

            # Get bus voltages
            key_buses = ["101", "108", "610", "sourcebus"]
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
            raise Warning(f"Power flow did not converge at hour {current_hour}")

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
        results.append(result)

    # Convert to DataFrame
    df = pd.DataFrame(results)
    csv_path = os.path.join(
        os.getenv("DSS_EXPORT_FOLDER", ""), "daily_powerflow_hourly_results.csv"
    )
    df.to_csv(csv_path, index=False)
    print(f"Results saved to: {csv_path}")
    return df


if __name__ == "__main__":
    df = run_daily_powerflow()
    create_qsts_plots(df)
