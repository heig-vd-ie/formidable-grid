from main import get_profile_data

from app import create_qsts_plots, read_results, run_daily_powerflow

if __name__ == "__main__":
    profiles = get_profile_data()
    run_daily_powerflow(profiles=profiles)
    df = read_results()
    create_qsts_plots(df)
