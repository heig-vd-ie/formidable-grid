from app.helpers import setup_and_run_circuit
from app.plotter import plot_grid_topology, plot_monitor_results

if __name__ == "__main__":
    setup_and_run_circuit("Run_Dynamics.dss")
    plot_grid_topology(base_size_multiplier=0.1)
    plot_monitor_results()
