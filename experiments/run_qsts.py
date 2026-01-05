from main import read_profile_data

from data_display import create_qsts_plots
from data_extract import read_results
from opendss_indirect import run_qsts_powerflow

if __name__ == "__main__":
    profiles = read_profile_data()
    run_qsts_powerflow(profiles=profiles)
    df = read_results()
    create_qsts_plots(df)
