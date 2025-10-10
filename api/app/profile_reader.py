from datetime import datetime
import os
from pathlib import Path
import numpy as np
import pandas as pd
from common.setup_log import setup_logger

logger = setup_logger(__name__)


class ProfileReader:
    def __init__(self):
        self.INPUT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "inputs"
        self.OUTPUT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"

    def _plot_profile(
        self, x: pd.Series, y: pd.Series, title: str, y_label: str, output_filename: str
    ):
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
            )
        )
        fig.update_layout(
            title=title,
            xaxis_title="Datetime",
            yaxis_title=y_label,
            legend_title="Legend",
            template="plotly_white",
        )
        output_path = self.OUTPUT_DATA_DIR / output_filename
        fig.write_html(output_path)
        logger.info(f"Saved PV profile multipliers plot to {output_path}")

    def _pv_profile(
        self,
        file_name: str = "pv_profiles.parquet",
        to_plot: bool = False,
    ):
        """Load and process the PV profile data"""
        df = pd.read_parquet(self.INPUT_DATA_DIR / file_name)
        df["multiplier"] = df["PV"] / df["PV"].max()

        if to_plot:
            self._plot_profile(
                x=df.tail(100000)["Datetime"],
                y=df.tail(100000)["PV"],
                title="PV Profile Multipliers",
                y_label="Multiplier",
                output_filename="pv_profile_multipliers.html",
            )

    def _load_profile(
        self,
        file_name: str = "load_profiles.parquet",
        to_plot: bool = False,
    ):
        """Load and process the load profile data"""
        df = pd.read_parquet(self.INPUT_DATA_DIR / file_name)
        df["multiplier11"] = df["Blue.P1.Avg"] / df["Blue.P1.Avg"].max()
        df["multiplier12"] = df["Blue.P2.Avg"] / df["Blue.P2.Avg"].max()
        df["multiplier13"] = df["Blue.P3.Avg"] / df["Blue.P3.Avg"].max()

        df["multiplier21"] = df["Red.P1.Avg"] / df["Red.P1.Avg"].max()
        df["multiplier22"] = df["Red.P2.Avg"] / df["Red.P2.Avg"].max()
        df["multiplier23"] = df["Red.P3.Avg"] / df["Red.P3.Avg"].max()

        if to_plot:
            self._plot_profile(
                x=df.tail(10000)["Datetime"],
                y=df.tail(10000)["multiplier11"],
                title="Load Profile Multipliers",
                y_label="Multiplier",
                output_filename="load_profile_multipliers.html",
            )

    # df["curr_datetime"] = pd.to_datetime(df["curr_datetime"], format="%m/%d/%Y  %H:%M")
    # df = df.sort_values("curr_datetime")

    # # Create a full datetime index for every minute in the year (non-leap year)
    # start = datetime(
    #     df["curr_datetime"].dt.year.min(),
    #     df["curr_datetime"].dt.month.min(),
    #     df["curr_datetime"].dt.day.min(),
    # )
    # end = datetime(df["curr_datetime"].dt.year.min(), 12, 31, 23, 59)
    # full_index = pd.date_range(start, end, freq="min")

    # # Reindex and interpolate
    # df_interp = df.set_index("curr_datetime").reindex(full_index)
    # df_interp["multiplier"] = (
    #     df_interp["multiplier"].interpolate(method="time").fillna(0)
    # )

    # overall_avg = df["multiplier"].mean()
    # df_interp["multiplier"] = df_interp["multiplier"].fillna(overall_avg)

    # # Set the first element to the average value for its day
    # first_day = full_index[0].date()
    # first_day_mask = [dt.date() == first_day for dt in df["curr_datetime"]]
    # first_day_avg = df.loc[first_day_mask, "multiplier"].mean()
    # if not np.isnan(first_day_avg):
    #     df_interp.loc[df_interp.index[0], "multiplier"] = first_day_avg
    # else:
    #     df_interp.loc[df_interp.index[0], "multiplier"] = overall_avg

    # # Create the numpy array
    # multiplier_array = df_interp["multiplier"].to_numpy().flatten()
    # return multiplier_array


if __name__ == "__main__":
    profile_reader = ProfileReader()
    profile_reader._pv_profile(to_plot=True)
    profile_reader._load_profile(to_plot=True)
