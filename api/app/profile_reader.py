from datetime import datetime
import os

import numpy as np
import pandas as pd


def load_pv_profile(file_name: str = "PV_PROFILE.csv") -> np.ndarray:
    """Load and process the PV profile data"""
    df = pd.read_csv(f"{os.getenv('INTERNAL_DSSFILES_FOLDER')}/{file_name}")
    df["curr_datetime"] = df.apply(
        lambda row: f"{row['DATE (MM/DD/YYYY)']} {row['HST']}", axis=1
    )
    df["multiplier"] = (
        df["Global Horizontal [W/m^2]"] / df["Global Horizontal [W/m^2]"].max()
    )

    # Parse datetime column
    df["curr_datetime"] = pd.to_datetime(df["curr_datetime"], format="%m/%d/%Y  %H:%M")
    df = df.sort_values("curr_datetime")

    # Create a full datetime index for every minute in the year (non-leap year)
    start = datetime(
        df["curr_datetime"].dt.year.min(),
        df["curr_datetime"].dt.month.min(),
        df["curr_datetime"].dt.day.min(),
    )
    end = datetime(df["curr_datetime"].dt.year.min(), 12, 31, 23, 59)
    full_index = pd.date_range(start, end, freq="min")

    # Reindex and interpolate
    df_interp = df.set_index("curr_datetime").reindex(full_index)
    df_interp["multiplier"] = (
        df_interp["multiplier"].interpolate(method="time").fillna(0)
    )

    overall_avg = df["multiplier"].mean()
    df_interp["multiplier"] = df_interp["multiplier"].fillna(overall_avg)

    # Set the first element to the average value for its day
    first_day = full_index[0].date()
    first_day_mask = [dt.date() == first_day for dt in df["curr_datetime"]]
    first_day_avg = df.loc[first_day_mask, "multiplier"].mean()
    if not np.isnan(first_day_avg):
        df_interp.loc[df_interp.index[0], "multiplier"] = first_day_avg
    else:
        df_interp.loc[df_interp.index[0], "multiplier"] = overall_avg

    # Create the numpy array
    multiplier_array = df_interp["multiplier"].to_numpy().flatten()
    return multiplier_array
