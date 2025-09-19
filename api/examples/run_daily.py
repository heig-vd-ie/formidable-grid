from app import create_qsts_plots, run_daily_powerflow

if __name__ == "__main__":
    df = run_daily_powerflow()
    create_qsts_plots(df)
