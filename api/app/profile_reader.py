from pathlib import Path
import pandas as pd
from common.setup_log import setup_logger

logger = setup_logger(__name__)

HEAD_NUMBER = int(1e3)
MONTHTIME_FORMAT = "%m-%d %H:%M:%S"


class ProfileReader:
    def __init__(self):
        self.INPUT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "inputs"
        self.OUTPUT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"

    def _plot_profile(
        self,
        df: pd.DataFrame,
        x: str,
        ys: list[str],
        title: str,
        y_label: str,
        output_filename: str,
    ):
        import plotly.graph_objects as go

        df = df.copy().head(HEAD_NUMBER)

        fig = go.Figure()
        for y in ys:
            fig.add_trace(
                go.Scatter(
                    x=df.index if not x in df else df[x],
                    y=df[y],
                    mode="lines",
                    name=y,
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
        df["κp"] = df["PV"] / df["PV"].max()

        _pv = df[["Datetime", "κp"]].copy()
        _pv["year"] = _pv["Datetime"].dt.year
        _pv["Datetime"] = "2025-" + df["Datetime"].dt.strftime(MONTHTIME_FORMAT)
        _pv_pivot = _pv.pivot(index="Datetime", columns="year", values="κp")
        _pv_pivot.columns = [f"κp.{year}" for year in _pv_pivot.columns]

        self.pv = _pv_pivot
        logger.info(f"Loaded PV profile data with shape: {self.pv.shape}")

        if to_plot:
            self._plot_profile(
                df=self.pv,
                x="Datetime",
                ys=self.pv.columns.tolist(),
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
        _df = pd.read_parquet(self.INPUT_DATA_DIR / file_name)
        groups = ["Blue", "Red"]
        phases = ["1", "2", "3"]
        types = ["P", "Q"]

        _df = _df.groupby("Datetime").mean().reset_index()

        _df["year"] = _df["Datetime"].dt.year
        _df["Datetime"] = "2025-" + _df["Datetime"].dt.strftime(MONTHTIME_FORMAT)

        dfs = []
        for g in groups:
            for t in types:
                for p in phases:
                    col = f"{g}.{t}{p}.Avg"
                    temp_df = _df[["Datetime", "year", col]].copy()
                    temp_df[f"κ{t.lower()}{p.lower()}.{g[0].lower()}"] = (
                        temp_df[col] / temp_df[col].max()
                    )
                    _load = temp_df.pivot(
                        index="Datetime",
                        columns="year",
                        values=f"κ{t.lower()}{p.lower()}.{g[0].lower()}",
                    )
                    _load.columns = [
                        f"κ{t.lower()}{p.lower()}.{g[0].lower()}{year}"
                        for year in _load.columns
                    ]
                    dfs.append(_load)

        df = pd.concat(dfs, axis=1)
        df = df.reset_index()
        self.load = df[
            ["Datetime"]
            + [
                f"κ{t.lower()}{p.lower()}.{g[0].lower()}{year}"
                for g in groups
                for t in types
                for p in phases
                for year in _df["year"].unique()
            ]
        ]

        if to_plot:
            self._plot_profile(
                df=self.load,
                x="Datetime",
                ys=[
                    f"κ{t.lower()}{p.lower()}.{g[0].lower()}{year}"
                    for g in groups
                    for t in types
                    for p in phases
                    for year in _df["year"].unique()
                ],
                title="Load Profile Multipliers",
                y_label="Multiplier",
                output_filename="load_profile_multipliers.html",
            )

    def _handle_missing_values(self):
        """Handle missing values in the profiles"""
        print(self.pv.shape)
        print(self.load.shape)


if __name__ == "__main__":
    profile_reader = ProfileReader()
    profile_reader._pv_profile(to_plot=True)
    profile_reader._load_profile(to_plot=True)
    profile_reader._handle_missing_values()
