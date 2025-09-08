import os
from opendssdirect import dss, enums
import numpy as np

filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "GFL_IEEE123",
    "Run_IEEE123Bus_GFLDaily.dss",
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

    if len(monitor_data) > 1:  # Skip if no data
        data_array = np.array(monitor_data)

        plt.figure(figsize=(10, 6))
        for col in range(1, data_array.shape[1]):
            plt.plot(data_array[:, col], label=f"Channel {col}")

        plt.title(f"Monitor: {monitor_name}")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{monitor_name}.png")
