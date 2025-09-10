import os
import sys
from opendssdirect import dss

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opendss import plot_grid_topology, plot_monitor_results

# Load and solve the circuit
filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "Run_GFMDaily.dss",
)
print(f"Running OpenDSS file: {filepath}")

dss.Command("Clear")
dss.Command(f'Redirect "{filepath}"')

# Plot with adaptive sizing - you can adjust base_size_multiplier if needed
# Use values < 1.0 to make everything smaller, > 1.0 to make everything larger
# plot_grid_topology(base_size_multiplier=0.8)  # 20% smaller for better visibility

# Plot monitor results
plot_monitor_results()
