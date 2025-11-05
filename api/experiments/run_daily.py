from app import create_qsts_plots, read_results, run_daily_powerflow
from extract_data.profile_reader import ProfileReader

if __name__ == "__main__":
    run_daily_powerflow(
        profiles=ProfileReader().process_and_record_profiles().get_profiles()
    )
    df = read_results()
    create_qsts_plots(df)
