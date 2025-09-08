import os
from opendssdirect import dss, enums
import numpy as np

filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "GFM_IEEE123_MyStudy",
    "Run_IEEE123Bus_GFMDaily.dss",
)
print(f"Running OpenDSS file: {filepath}")

dss.run_command("Clear")
dss.run_command(f'Redirect "{filepath}"')

# Get monitor names and results
import matplotlib.pyplot as plt

monitor_names = dss.Monitors.AllNames()
for monitor_name in monitor_names:
    dss.Monitors.Name(monitor_name)
    monitor_data = dss.Monitors.AsMatrix()
    header = dss.Monitors.Header()

    if monitor_data is not None and len(monitor_data) > 1:  # Skip if no data
        data_array = np.array(monitor_data)

        # Extract time data (column 1 contains seconds)
        time_data = data_array[:, 1]

        plt.figure(figsize=(10, 6))
        # Start from column 2 since columns 0 and 1 are time data
        for col in range(2, data_array.shape[1]):
            # Use header names if available, otherwise fall back to generic labels
            header_index = col - 2  # Adjust index for header array
            if header and header_index < len(header):
                label = header[header_index]
            else:
                label = f"Channel {col-1}"
            plt.plot(time_data, data_array[:, col], label=label)

        plt.title(f"Monitor: {monitor_name}")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        plt.savefig(
            f"{os.path.join(os.path.dirname(__file__), 'Exports', f'{monitor_name}.png')}"
        )
