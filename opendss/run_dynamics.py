from helpers import setup_circuit
from plotter import plot_grid_topology, plot_monitor_results

if __name__ == "__main__":
    setup_circuit("Run_Dynamics.dss")
    plot_grid_topology(base_size_multiplier=0.1)
    plot_monitor_results()
