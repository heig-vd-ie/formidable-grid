import os
from opendssdirect import dss
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import plotly.graph_objects as go

matplotlib.use("Agg")  # Use non-interactive backend


def plot_grid_topology(base_size_multiplier=1.0):
    """Plot the grid topology using matplotlib with OpenDSS direct interface

    Args:
        base_size_multiplier (float): Global multiplier for all visual elements (default: 1.0)
                                    Use values < 1.0 to make everything smaller
                                    Use values > 1.0 to make everything larger
    """

    # Get all buses using OpenDSS direct interface
    bus_names = dss.Circuit.AllBusNames()
    if not bus_names:
        print("No buses found in circuit")
        return

    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(16, 12))

    # Get bus positions using OpenDSS Bus.X() and Bus.Y()
    bus_positions = {}
    all_x_coords = []
    all_y_coords = []

    for _, bus_name in enumerate(bus_names):
        # Set active bus and get coordinates from OpenDSS
        dss.Circuit.SetActiveBus(bus_name)
        x = dss.Bus.X()
        y = dss.Bus.Y()

        if x is None or y is None:
            raise ValueError(f"Could not get coordinates for bus {bus_name}")

        bus_positions[bus_name] = (x, y)
        all_x_coords.append(x)
        all_y_coords.append(y)

    # Calculate coordinate bounds and scaling factors
    if all_x_coords and all_y_coords:
        x_min, x_max = min(all_x_coords), max(all_x_coords)
        y_min, y_max = min(all_y_coords), max(all_y_coords)

        # Calculate the coordinate area dimensions
        coord_width = x_max - x_min if x_max != x_min else 1000
        coord_height = y_max - y_min if y_max != y_min else 1000

        # Calculate scale factor based on coordinate span
        # For power grid coordinates, we need to consider both the span AND absolute values
        max_dimension = max(coord_width, coord_height)

        # Check if we're dealing with geographic coordinates (large absolute values)
        avg_coord = (abs(x_min) + abs(x_max) + abs(y_min) + abs(y_max)) / 4
        is_geographic = avg_coord > 100000  # Likely geographic/UTM coordinates

        scale_factor = (10 if is_geographic else 10000) / max_dimension

        bus_radius = 25 * scale_factor * base_size_multiplier
        text_offset_y = 60.0 * scale_factor * base_size_multiplier
        transformer_radius = 15 * scale_factor * base_size_multiplier
        text_offset_transformer = 30 * scale_factor * base_size_multiplier
        line_width = max(0.5, 2 * scale_factor * base_size_multiplier)
        transformer_line_width = max(1.0, 4 * scale_factor * base_size_multiplier)
        font_size_bus = max(4, min(14, 8 * scale_factor * base_size_multiplier))
        font_size_line = max(0.1, min(12, 6 * scale_factor * base_size_multiplier))
        font_size_transformer = max(4, min(14, 8 * scale_factor * base_size_multiplier))

    else:
        raise ValueError("Could not determine coordinate bounds")

    for bus_name, (x, y) in bus_positions.items():
        circle = patches.Circle((x, y), bus_radius, color="blue", alpha=0.7)
        ax.add_patch(circle)

        clean_name = bus_name.split(".")[0] if "." in bus_name else bus_name
        ax.text(
            x,
            y - text_offset_y,
            clean_name,
            ha="center",
            va="top",
            fontsize=font_size_bus,
            fontweight="bold",
        )

    line_names = dss.Lines.AllNames()
    if not line_names:
        line_names = []

    for line_name in line_names:
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

            # Plot line with dynamic line width
            ax.plot([x1, x2], [y1, y2], "k-", linewidth=line_width, alpha=0.8)

            # Add line label at midpoint with dynamic font size
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
                fontsize=font_size_line,
                rotation=angle,
                bbox=dict(
                    boxstyle="round,pad=0.1",
                    facecolor="white",
                    alpha=0.7,
                    edgecolor="none",
                ),
            )

    # Get and plot all transformers using OpenDSS direct interface
    transformer_names = dss.Transformers.AllNames()
    if not transformer_names:
        transformer_names = []

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

                # Plot transformer as a thick red line with dynamic line width
                ax.plot(
                    [x1, x2],
                    [y1, y2],
                    "r-",
                    linewidth=transformer_line_width,
                    alpha=0.8,
                )

                # Add transformer symbols (circles at each end) with dynamic sizing
                circle1 = patches.Circle(
                    (x1, y1), transformer_radius, color="red", alpha=0.9
                )
                circle2 = patches.Circle(
                    (x2, y2), transformer_radius, color="red", alpha=0.9
                )
                ax.add_patch(circle1)
                ax.add_patch(circle2)

                # Add transformer label with dynamic positioning and font size
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                ax.text(
                    mid_x,
                    mid_y + text_offset_transformer,
                    transformer_name,
                    ha="center",
                    va="center",
                    fontsize=font_size_transformer,
                    fontweight="bold",
                    color="red",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.8),
                )

    # Set plot properties
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title(
        f"Test Feeder Grid Topology\n{len(bus_names)} Buses, {len(line_names)} Lines, {len(transformer_names)} Transformers",
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
        Line2D(
            [0], [0], color="red", label="Transformer", linewidth=transformer_line_width
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    # Adjust layout
    plt.tight_layout()

    # Save the plot as both SVG and HTML
    svg_path = os.path.join(
        os.path.dirname(__file__), "Exports", "network_topology.svg"
    )
    plt.savefig(svg_path, format="svg", dpi=300, bbox_inches="tight")
    print(f"Grid topology plot (SVG) saved to: {svg_path}")

    plt.close(fig)


def plot_monitor_results():
    """Plot monitor results using OpenDSS direct interface with Plotly"""

    # Get all monitor names
    monitor_names = dss.Monitors.AllNames()
    if not monitor_names:
        print("No monitors found in the circuit")
        return
    for monitor_name in monitor_names:
        # Set active monitor
        dss.Monitors.Name(monitor_name)

        # Get monitor data
        monitor_data = dss.Monitors.AsMatrix()
        header = dss.Monitors.Header()

        if monitor_data is not None and len(monitor_data) > 1:
            data_array = np.array(monitor_data)

            # Extract time data (usually in column 1)
            time_data = (
                data_array[:, 1]
                if data_array.shape[1] > 1
                else np.arange(len(data_array))
            )

            # Create Plotly figure for this monitor with professional styling
            fig = go.Figure()

            # Define color palette for different channels
            colors = [
                "rgba(31, 119, 180, 0.8)",  # Blue
                "rgba(255, 127, 14, 0.8)",  # Orange
                "rgba(44, 160, 44, 0.8)",  # Green
                "rgba(214, 39, 40, 0.8)",  # Red
                "rgba(148, 103, 189, 0.8)",  # Purple
                "rgba(140, 86, 75, 0.8)",  # Brown
            ]

            # Plot each channel (starting from column 2, skipping time columns)
            start_col = 2 if data_array.shape[1] > 2 else 1

            for i, col in enumerate(
                range(start_col, min(data_array.shape[1], start_col + 6))
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
                        line=dict(width=2.5, color=colors[i % len(colors)]),
                        hovertemplate=f"<b>{label}</b><br>Time: %{{x:.3f}}s<br>Value: %{{y:.3f}}<extra></extra>",
                    )
                )

            # Update layout with professional styling
            fig.update_layout(
                title=dict(
                    text=f"Monitor Results: {monitor_name}",
                    font=dict(size=16, color="rgba(25, 25, 112, 0.9)"),
                    x=0.5,
                ),
                xaxis=dict(
                    title="Time (seconds)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128, 128, 128, 0.2)",
                    zeroline=True,
                    zerolinecolor="rgba(128, 128, 128, 0.3)",
                    tickfont=dict(size=11),
                ),
                yaxis=dict(
                    title="Value",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128, 128, 128, 0.2)",
                    zeroline=True,
                    zerolinecolor="rgba(128, 128, 128, 0.3)",
                    tickfont=dict(size=11),
                ),
                showlegend=True,
                legend=dict(
                    x=1.02,
                    y=1,
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="rgba(128, 128, 128, 0.5)",
                    borderwidth=1,
                    font=dict(size=11),
                ),
                width=1200,
                height=700,
                hovermode="x unified",
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=60, r=120, t=80, b=60),
            )

            # Save the plot
            output_path = os.path.join(
                os.path.dirname(__file__), "Exports", f"{monitor_name}_results.html"
            )
            fig.write_html(output_path)
            print(f"Monitor plot saved to: {output_path}")

        else:
            print(f"No data found for monitor {monitor_name}")
