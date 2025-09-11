import os
import sys
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from opendssdirect import dss
from datetime import datetime, timedelta

from opendss.helpers import replace_env_vars_in_dss

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_circuit():
    """Initialize and setup the OpenDSS circuit"""
    filepath = os.path.join(
        os.path.dirname(__file__),
        "DSSfiles",
        "Run_QSTS.dss",
    )
    print(f"Loading OpenDSS file: {filepath}")

    temp_file = replace_env_vars_in_dss(filepath)

    dss.Command("Clear")
    dss.Command(f'Redirect "{temp_file}"')

    os.remove(temp_file)
    print(f"Temp file {temp_file} removed.")


def run_daily_powerflow():
    """Run power flow analysis for each hour of a day"""
    print("Starting daily power flow analysis with hourly resolution...")

    # Setup circuit
    setup_circuit()

    # Data storage
    results = []

    # Time parameters
    total_minutes = 24  # 24 hours * 60 minutes
    start_time = datetime.now()

    print(f"Running power flow for {total_minutes} minutes (once per minute)...")
    print("This will solve the power flow 1440 times for a full day.")

    # Main simulation loop
    for minute in range(total_minutes):
        # Calculate current time
        current_hour = minute
        current_minute = 0
        current_second = 0

        # Set time in OpenDSS (hour, second_of_hour)
        dss.run_command(f"Set time=({current_hour},0)")

        # Solve power flow
        solve_start = time.time()
        dss.run_command("Solve")
        solve_time = time.time() - solve_start

        # Check if solution converged
        converged = dss.Solution.Converged()

        # Collect data
        if converged:
            # Get system-level data
            total_power = dss.Circuit.TotalPower()
            losses = dss.Circuit.Losses()

            # Get bus voltages (sample key buses)
            key_buses = ["101", "108", "610", "sourcebus"]
            bus_voltages = {}

            for bus in key_buses:
                try:
                    dss.Circuit.SetActiveBus(bus)
                    voltages = dss.Bus.Voltages()
                    if voltages:
                        # Calculate magnitude for phase A (first two elements are real and imaginary)
                        voltage_mag = (
                            np.sqrt(voltages[0] ** 2 + voltages[1] ** 2)
                            if len(voltages) >= 2
                            else 0
                        )
                        bus_voltages[f"V_{bus}"] = voltage_mag
                    else:
                        bus_voltages[f"V_{bus}"] = 0
                except:
                    bus_voltages[f"V_{bus}"] = 0

            # Get PV and Storage data
            try:
                dss.Circuit.SetActiveElement("PVSystem.myPV")
                pv_power = dss.CktElement.Powers()
                pv_real_power = pv_power[0] if pv_power else 0
                pv_reactive_power = pv_power[1] if len(pv_power) > 1 else 0
            except:
                pv_real_power = pv_reactive_power = 0

            try:
                dss.Circuit.SetActiveElement("Storage.mystorage")
                storage_power = dss.CktElement.Powers()
                storage_real_power = storage_power[0] if storage_power else 0
                storage_reactive_power = (
                    storage_power[1] if len(storage_power) > 1 else 0
                )
            except:
                storage_real_power = storage_reactive_power = 0
        else:
            # If not converged, set values to NaN
            total_power = [float("nan"), float("nan")]
            losses = [float("nan"), float("nan")]
            bus_voltages = {f"V_{bus}": float("nan") for bus in key_buses}
            pv_real_power = pv_reactive_power = float("nan")
            storage_real_power = storage_reactive_power = float("nan")

        # Store results
        result = {
            "time_hour": current_hour,
            "hour": current_hour,
            "minute": current_minute,
            "second": current_second,
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

        # Progress reporting
        elapsed = time.time() - start_time.timestamp()
        progress = ((minute + 1) / total_minutes) * 100
        eta = (
            (elapsed / (minute + 1)) * (total_minutes - minute - 1) if minute > 0 else 0
        )
        print(
            f"Minute {current_minute:2d}: {progress:5.1f}% complete | "
            f"Solve time: {solve_time*1000:.2f}ms | "
            f"Converged: {converged} | "
            f"ETA: {eta/60:.1f} min"
        )

    total_elapsed = time.time() - start_time.timestamp()
    print(f"\nSimulation completed in {total_elapsed/60:.2f} minutes")
    print(f"Average solve time: {np.mean([r['solve_time_ms'] for r in results]):.2f}ms")

    # Convert to DataFrame
    df = pd.DataFrame(results)
    return df


def create_plots(df):
    """Create comprehensive plots of the power flow results"""
    print("Creating plots...")

    # Create subplots
    fig = make_subplots(
        rows=4,
        cols=2,
        subplot_titles=(
            "System Total Power vs Time",
            "Bus Voltages vs Time",
            "PV System Power vs Time",
            "Storage System Power vs Time",
            "System Losses vs Time",
            "Solution Performance",
            "Power Balance",
            "Convergence Statistics",
        ),
        specs=[
            [{"secondary_y": True}, {"secondary_y": False}],
            [{"secondary_y": True}, {"secondary_y": True}],
            [{"secondary_y": True}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    # 1. System Total Power
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["total_real_power_kW"],
            name="Real Power (kW)",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["total_reactive_power_kVAr"],
            name="Reactive Power (kVAr)",
            line=dict(color="red"),
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

    # 2. Bus Voltages
    voltage_cols = [col for col in df.columns if col.startswith("V_")]
    colors = px.colors.qualitative.Set1
    for i, col in enumerate(voltage_cols):
        bus_name = col.replace("V_", "")
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df[col],
                name=f"Bus {bus_name}",
                line=dict(color=colors[i % len(colors)]),
            ),
            row=1,
            col=2,
        )

    # 3. PV System Power
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["pv_real_power_kW"],
            name="PV Real Power (kW)",
            line=dict(color="orange"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["pv_reactive_power_kVAr"],
            name="PV Reactive Power (kVAr)",
            line=dict(color="yellow"),
        ),
        row=2,
        col=1,
        secondary_y=True,
    )

    # 4. Storage System Power
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["storage_real_power_kW"],
            name="Storage Real Power (kW)",
            line=dict(color="green"),
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["storage_reactive_power_kVAr"],
            name="Storage Reactive Power (kVAr)",
            line=dict(color="lightgreen"),
        ),
        row=2,
        col=2,
        secondary_y=True,
    )

    # 5. System Losses
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["losses_real_kW"],
            name="Real Losses (kW)",
            line=dict(color="red"),
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["losses_reactive_kVAr"],
            name="Reactive Losses (kVAr)",
            line=dict(color="pink"),
        ),
        row=3,
        col=1,
        secondary_y=True,
    )

    # 6. Solution Performance
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["solve_time_ms"],
            name="Solve Time (ms)",
            line=dict(color="purple"),
        ),
        row=3,
        col=2,
    )

    # 7. Power Balance
    net_power = (
        df["total_real_power_kW"] - df["pv_real_power_kW"] - df["storage_real_power_kW"]
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=net_power,
            name="Net Load (kW)",
            line=dict(color="brown"),
        ),
        row=4,
        col=1,
    )

    # 8. Convergence Statistics
    convergence_rate = (
        df["converged"].rolling(window=6).mean() * 100
    )  # 6-hour rolling convergence rate
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=convergence_rate,
            name="Convergence Rate (%)",
            line=dict(color="black"),
        ),
        row=4,
        col=2,
    )

    # Update layout
    fig.update_layout(
        height=1200,
        title_text="Daily Power Flow Analysis - Hourly Resolution",
        showlegend=True,
    )

    # Update x-axis labels
    for i in range(1, 5):
        for j in range(1, 3):
            fig.update_xaxes(title_text="Time", row=i, col=j)

    return fig


def save_results(df, fig):
    """Save results to CSV and plot to HTML"""
    exports_dir = os.path.join(os.path.dirname(__file__), "Exports")
    os.makedirs(exports_dir, exist_ok=True)

    # Save DataFrame to CSV
    csv_path = os.path.join(exports_dir, "daily_powerflow_hourly_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"Results saved to: {csv_path}")

    # Save plot to HTML
    html_path = os.path.join(exports_dir, "daily_powerflow_hourly_plots.html")
    fig.write_html(html_path)
    print(f"Interactive plots saved to: {html_path}")

    # Print summary statistics
    print("\n=== SIMULATION SUMMARY ===")
    print(f"Total simulation points: {len(df)}")
    print(f"Convergence rate: {df['converged'].mean()*100:.2f}%")
    print(f"Average solve time: {df['solve_time_ms'].mean():.2f} ms")
    print(f"Max solve time: {df['solve_time_ms'].max():.2f} ms")
    print(f"Min solve time: {df['solve_time_ms'].min():.2f} ms")
    print(f"Average real power: {df['total_real_power_kW'].mean():.2f} kW")
    print(f"Peak real power: {df['total_real_power_kW'].max():.2f} kW")
    print(f"Average losses: {df['losses_real_kW'].mean():.2f} kW")


def main():
    """Main function to run the daily power flow analysis"""
    print("=" * 60)
    print("DAILY POWER FLOW ANALYSIS - HOURLY RESOLUTION")
    print("=" * 60)

    try:
        # Run the simulation
        df = run_daily_powerflow()

        # Create plots
        fig = create_plots(df)

        # Save results
        save_results(df, fig)

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
