from main import read_profile_data

from app import create_qsts_plots, read_results, run_qsts_powerflow

if __name__ == "__main__":
    profiles = read_profile_data()
    run_qsts_powerflow(profiles=profiles)
    df = read_results()
    create_qsts_plots(df)
