from app import create_qsts_plots, read_results, run_daily_powerflow

if __name__ == "__main__":
    run_daily_powerflow()
    df = read_results()
    create_qsts_plots(df)
