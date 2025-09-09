import os
import sys
from opendssdirect import dss

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opendss import plot_grid_topology, plot_monitor_results

# Load and solve the circuit
filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "Run_IEEE123Bus_GFMDaily.dss",
)
print(f"Running OpenDSS file: {filepath}")

dss.run_command("Clear")
dss.run_command(f'Redirect "{filepath}"')

plot_grid_topology()

# Plot monitor results
plot_monitor_results()
