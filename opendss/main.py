import os
from opendssdirect import dss
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

# Load and solve the circuit
filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "Run_IEEE123Bus_GFMDaily.dss",
)
print(f"Running OpenDSS file: {filepath}")

dss.run_command("Clear")
dss.run_command(f'Redirect "{filepath}"')
dss.run_command("Solve")


def plot_grid_topology():
    """Plot the grid topology using only OpenDSS direct interface"""
    fig, ax = plt.subplots(figsize=(16, 12))

    # Get all buses using OpenDSS direct interface
    bus_names = dss.Circuit.AllBusNames()
    if not bus_names:
        print("No buses found in circuit")
        return

    print(f"Found {len(bus_names)} buses in the circuit")

    # Get bus positions using OpenDSS Bus.X() and Bus.Y()
    bus_positions = {}

    for i, bus_name in enumerate(bus_names):
        # Set active bus and get coordinates from OpenDSS
        dss.Circuit.SetActiveBus(bus_name)
        x = dss.Bus.X()
        y = dss.Bus.Y()

        # Convert to float and handle None values
        x = float(x) if x is not None else 0.0
        y = float(y) if y is not None else 0.0

        # If coordinates are 0,0 (not set), use automatic layout
        if x == 0.0 and y == 0.0:
            cols = int(np.sqrt(len(bus_names))) + 1
            x = float((i % cols) * 300)
            y = float((i // cols) * 300)

        bus_positions[bus_name] = (x, y)

        # Plot bus as a circle
        circle = Circle((x, y), 25, color="blue", alpha=0.7)
        ax.add_patch(circle)

        # Clean bus name for display
        clean_name = bus_name.split(".")[0] if "." in bus_name else bus_name
        ax.text(
            x,
            y - 60.0,
            clean_name,
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
        )

    # Get and plot all lines using OpenDSS direct interface
    line_names = dss.Lines.AllNames()
    if not line_names:
        line_names = []

    print(f"Found {len(line_names)} lines in the circuit")

    for line_name in line_names:
        # Set active line and get bus connections
        dss.Lines.Name(line_name)
        bus1 = dss.Lines.Bus1()
        bus2 = dss.Lines.Bus2()

        if not bus1 or not bus2:
            continue

        # Clean bus names (remove phase information)
        bus1_clean = bus1.split(".")[0] if "." in bus1 else bus1
        bus2_clean = bus2.split(".")[0] if "." in bus2 else bus2

        # Find matching buses in our bus list
        bus1_full = None
        bus2_full = None

        for bus in bus_names:
            bus_clean = bus.split(".")[0] if "." in bus else bus
            if bus_clean == bus1_clean:
                bus1_full = bus
            if bus_clean == bus2_clean:
                bus2_full = bus

        if (
            bus1_full
            and bus2_full
            and bus1_full in bus_positions
            and bus2_full in bus_positions
        ):
            x1, y1 = bus_positions[bus1_full]
            x2, y2 = bus_positions[bus2_full]

            # Plot line
            ax.plot([x1, x2], [y1, y2], "k-", linewidth=2, alpha=0.8)

            # Add line label at midpoint
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            if x2 != x1:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            else:
                angle = 90
            ax.text(
                mid_x,
                mid_y,
                line_name,
                ha="center",
                va="center",
                fontsize=6,
                rotation=angle,
                bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7),
            )

    # Get and plot all transformers using OpenDSS direct interface
    transformer_names = dss.Transformers.AllNames()
    if not transformer_names:
        transformer_names = []

    print(f"Found {len(transformer_names)} transformers in the circuit")

    for transformer_name in transformer_names:
        # Set active transformer
        dss.Transformers.Name(transformer_name)

        # Get the buses directly from the transformer definition
        # Use circuit element interface to get bus names
        dss.Circuit.SetActiveElement(f"Transformer.{transformer_name}")
        bus_names_str = dss.CktElement.BusNames()

        if bus_names_str and len(bus_names_str) >= 2:
            bus1 = bus_names_str[0].split(".")[0]
            bus2 = bus_names_str[1].split(".")[0]

            # Find matching buses
            bus1_full = None
            bus2_full = None

            for bus in bus_names:
                bus_clean = bus.split(".")[0] if "." in bus else bus
                if bus_clean == bus1:
                    bus1_full = bus
                if bus_clean == bus2:
                    bus2_full = bus

            if (
                bus1_full
                and bus2_full
                and bus1_full in bus_positions
                and bus2_full in bus_positions
            ):
                x1, y1 = bus_positions[bus1_full]
                x2, y2 = bus_positions[bus2_full]

                # Plot transformer as a thick red line
                ax.plot([x1, x2], [y1, y2], "r-", linewidth=4, alpha=0.8)

                # Add transformer symbols (circles at each end)
                circle1 = Circle((x1, y1), 15, color="red", alpha=0.9)
                circle2 = Circle((x2, y2), 15, color="red", alpha=0.9)
                ax.add_patch(circle1)
                ax.add_patch(circle2)

                # Add transformer label
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                ax.text(
                    mid_x,
                    mid_y + 30,
                    transformer_name,
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight="bold",
                    color="red",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.8),
                )

    # Set plot properties
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title(
        f"IEEE 123-Bus Test Feeder Grid Topology (OpenDSS Direct)\n{len(bus_names)} Buses, {len(line_names)} Lines, {len(transformer_names)} Transformers",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

    # Add legend
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="blue",
            label="Bus",
            markersize=8,
            linestyle="None",
        ),
        Line2D([0], [0], color="black", label="Line", linewidth=2),
        Line2D([0], [0], color="red", label="Transformer", linewidth=4),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    # Adjust layout and save
    plt.tight_layout()

    # Save the plot
    output_path = os.path.join(
        os.path.dirname(__file__), "Exports", "network_topology.png"
    )
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Grid topology plot saved to: {output_path}")

    plt.show()


def print_network_info():
    """Print detailed network information using OpenDSS direct interface"""
    print("\n" + "=" * 60)
    print("NETWORK INFORMATION SUMMARY (OpenDSS Direct)")
    print("=" * 60)

    # Circuit info
    print(f"Circuit Name: {dss.Circuit.Name()}")
    print(f"Number of Buses: {dss.Circuit.NumBuses()}")
    print(f"Number of Nodes: {dss.Circuit.NumNodes()}")

    # Bus information
    bus_names = dss.Circuit.AllBusNames()
    if bus_names:
        print(f"\nBuses ({len(bus_names)}):")
        for i, bus in enumerate(bus_names[:10]):  # Show first 10
            print(f"  {i+1:3d}. {bus}")
        if len(bus_names) > 10:
            print(f"  ... and {len(bus_names)-10} more buses")

    # Line information
    line_names = dss.Lines.AllNames()
    if line_names:
        print(f"\nLines ({len(line_names)}):")
        for i, line in enumerate(line_names[:10]):  # Show first 10
            dss.Lines.Name(line)
            bus1 = dss.Lines.Bus1()
            bus2 = dss.Lines.Bus2()
            length = dss.Lines.Length()
            print(f"  {i+1:3d}. {line}: {bus1} -> {bus2} ({length:.2f} units)")
        if len(line_names) > 10:
            print(f"  ... and {len(line_names)-10} more lines")

    # Transformer information
    transformer_names = dss.Transformers.AllNames()
    if transformer_names:
        print(f"\nTransformers ({len(transformer_names)}):")
        for i, transformer in enumerate(transformer_names):
            dss.Circuit.SetActiveElement(f"Transformer.{transformer}")
            bus_names_list = dss.CktElement.BusNames()
            print(
                f"  {i+1:3d}. {transformer}: {' -> '.join(bus_names_list) if bus_names_list else 'N/A'}"
            )


def plot_monitor_results():
    """Plot monitor results using OpenDSS direct interface"""
    print("\n" + "=" * 60)
    print("PLOTTING MONITOR RESULTS")
    print("=" * 60)

    # Get all monitor names
    monitor_names = dss.Monitors.AllNames()
    if not monitor_names:
        print("No monitors found in the circuit")
        return

    print(f"Found {len(monitor_names)} monitors in the circuit")

    for monitor_name in monitor_names:
        print(f"\nProcessing monitor: {monitor_name}")

        # Set active monitor
        dss.Monitors.Name(monitor_name)

        # Get monitor data
        monitor_data = dss.Monitors.AsMatrix()
        header = dss.Monitors.Header()

        if monitor_data is not None and len(monitor_data) > 1:
            data_array = np.array(monitor_data)
            print(f"  Data shape: {data_array.shape}")

            # Extract time data (usually in column 1)
            time_data = (
                data_array[:, 1]
                if data_array.shape[1] > 1
                else np.arange(len(data_array))
            )

            # Create figure for this monitor
            plt.figure(figsize=(12, 8))

            # Plot each channel (starting from column 2, skipping time columns)
            start_col = 2 if data_array.shape[1] > 2 else 1

            for col in range(
                start_col, min(data_array.shape[1], start_col + 6)
            ):  # Limit to 6 channels for readability
                # Get header name if available
                header_index = col - 2  # Adjust for header indexing
                if header and header_index < len(header):
                    label = header[header_index]
                else:
                    label = f"Channel {col-1}"

                plt.plot(time_data, data_array[:, col], label=label, linewidth=2)

            plt.title(f"Monitor: {monitor_name}", fontsize=14, fontweight="bold")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Value")
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(
                os.path.dirname(__file__), "Exports", f"{monitor_name}_results.png"
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"  Monitor plot saved to: {output_path}")

            plt.show()

            # Print some statistics
            if data_array.shape[1] > 2:
                print(
                    f"  Time range: {time_data[0]:.2f} to {time_data[-1]:.2f} seconds"
                )
                print(f"  Number of data points: {len(time_data)}")
                if header:
                    print(
                        f"  Channels: {', '.join(header[:6])}"
                    )  # Show first 6 channel names
        else:
            print(f"  No data found for monitor {monitor_name}")


# Generate the grid topology plot and print info
plot_grid_topology()
print_network_info()

# Plot monitor results
plot_monitor_results()
