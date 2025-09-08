import os
from opendssdirect import dss
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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
    """Plot the grid topology using only OpenDSS direct interface with Plotly"""

    # Get all buses using OpenDSS direct interface
    bus_names = dss.Circuit.AllBusNames()
    if not bus_names:
        print("No buses found in circuit")
        return

    print(f"Found {len(bus_names)} buses in the circuit")

    # Get bus positions using OpenDSS Bus.X() and Bus.Y()
    bus_positions = {}
    bus_x = []
    bus_y = []
    bus_labels = []

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
        bus_x.append(x)
        bus_y.append(y)

        # Clean bus name for display
        clean_name = bus_name.split(".")[0] if "." in bus_name else bus_name
        bus_labels.append(clean_name)

    # Get and plot all lines using OpenDSS direct interface
    line_names = dss.Lines.AllNames()
    if not line_names:
        line_names = []

    print(f"Found {len(line_names)} lines in the circuit")

    # Prepare line data
    line_x = []
    line_y = []
    line_labels = []

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

            # Add line coordinates
            line_x.extend([x1, x2, None])  # None creates a break in the line
            line_y.extend([y1, y2, None])
            line_labels.append(line_name)

    # Get and plot all transformers using OpenDSS direct interface
    transformer_names = dss.Transformers.AllNames()
    if not transformer_names:
        transformer_names = []

    print(f"Found {len(transformer_names)} transformers in the circuit")

    # Prepare transformer data
    transformer_x = []
    transformer_y = []
    transformer_labels = []

    for transformer_name in transformer_names:
        # Set active transformer
        dss.Transformers.Name(transformer_name)

        # Get the buses directly from the transformer definition
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

                # Add transformer coordinates
                transformer_x.extend([x1, x2, None])
                transformer_y.extend([y1, y2, None])
                transformer_labels.append(transformer_name)

    # Create Plotly figure
    fig = go.Figure()

    # Add lines
    if line_x:
        fig.add_trace(
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                line=dict(color="black", width=2),
                name="Lines",
                hoverinfo="skip",
            )
        )

    # Add transformers
    if transformer_x:
        fig.add_trace(
            go.Scatter(
                x=transformer_x,
                y=transformer_y,
                mode="lines",
                line=dict(color="red", width=6),
                name="Transformers",
                hoverinfo="skip",
            )
        )

    # Add buses
    fig.add_trace(
        go.Scatter(
            x=bus_x,
            y=bus_y,
            mode="markers+text",
            marker=dict(size=20, color="blue", opacity=0.7),
            text=bus_labels,
            textposition="bottom center",
            name="Buses",
            hovertemplate="<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        title=f"IEEE 123-Bus Test Feeder Grid Topology (OpenDSS Direct)<br>{len(bus_names)} Buses, {len(line_names)} Lines, {len(transformer_names)} Transformers",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        showlegend=True,
        width=1200,
        height=800,
        hovermode="closest",
    )

    # Set equal aspect ratio
    fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    # Save the plot
    output_path = os.path.join(
        os.path.dirname(__file__), "Exports", "network_topology.html"
    )
    fig.write_html(output_path)
    print(f"Grid topology plot saved to: {output_path}")

    # Also save as PNG
    try:
        png_path = os.path.join(
            os.path.dirname(__file__), "Exports", "network_topology.png"
        )
        fig.write_image(png_path, width=1200, height=800, scale=2)
        print(f"Grid topology plot (PNG) saved to: {png_path}")
    except Exception as e:
        print(f"Could not save PNG (install kaleido for PNG export): {e}")

    # Show the plot
    fig.show()


def plot_monitor_results():
    """Plot monitor results using OpenDSS direct interface with Plotly"""
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

            # Create Plotly figure for this monitor
            fig = go.Figure()

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

                fig.add_trace(
                    go.Scatter(
                        x=time_data,
                        y=data_array[:, col],
                        mode="lines",
                        name=label,
                        line=dict(width=2),
                    )
                )

            # Update layout
            fig.update_layout(
                title=f"Monitor: {monitor_name}",
                xaxis_title="Time (seconds)",
                yaxis_title="Value",
                showlegend=True,
                width=1000,
                height=600,
                hovermode="x unified",
            )

            # Save the plot
            output_path = os.path.join(
                os.path.dirname(__file__), "Exports", f"{monitor_name}_results.html"
            )
            fig.write_html(output_path)
            print(f"  Monitor plot saved to: {output_path}")

            # Also save as PNG if possible
            try:
                png_path = os.path.join(
                    os.path.dirname(__file__), "Exports", f"{monitor_name}_results.png"
                )
                fig.write_image(png_path, width=1000, height=600, scale=2)
                print(f"  Monitor plot (PNG) saved to: {png_path}")
            except Exception as e:
                print(f"  Could not save PNG (install kaleido for PNG export): {e}")

            fig.show()

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


# Generate the grid topology plot and print info
plot_grid_topology()
print_network_info()

# Plot monitor results
plot_monitor_results()
