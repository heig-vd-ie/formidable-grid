import os
from pathlib import Path
from opendssdirect import dss
from helpers import replace_env_vars_in_dss
from plotter import plot_grid_topology, plot_monitor_results

filepath = Path(os.getenv("INTERNAL_DSSFILES_FOLDER", "")) / "Run_Dynamics.dss"

temp_file = replace_env_vars_in_dss(filepath)

dss.Command("Clear")
dss.Command(f'Redirect "{temp_file}"')

os.remove(temp_file)
print(f"Temp file {temp_file} removed.")

plot_grid_topology(base_size_multiplier=0.1)

plot_monitor_results()
