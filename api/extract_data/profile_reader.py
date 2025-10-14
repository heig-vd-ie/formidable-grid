from pathlib import Path
import pandas as pd
from common.setup_log import setup_logger
from config import settings

logger = setup_logger(__name__)

HEAD_NUMBER = int(1e4)
MONTHTIME_FORMAT = "%m-%d %H:%M:%S"


class ProfileReader:
    def __init__(self):
        self.INPUT_DATA_DIR = (
            Path(__file__).parent.parent.parent / settings.profile_data.folder_path
        )
        self.OUTPUT_DATA_DIR = (
            Path(__file__).parent.parent.parent
            / settings.profile_data.output_folder_path
        )

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
        file_name: str = settings.profile_data.pv_profile_file,
        to_plot: bool = False,
    ):
        """Load and process the PV profile data"""
        df = pd.read_parquet(self.INPUT_DATA_DIR / file_name)
        df["κp"] = df["PV"] / df["PV"].max()

        _pv = df[["Datetime", "κp"]].copy()
        _pv["year"] = _pv["Datetime"].dt.year
        _pv["Datetime"] = "2025-" + df["Datetime"].dt.strftime(MONTHTIME_FORMAT)
        _pv = _pv.pivot(index="Datetime", columns="year", values="κp")
        _pv.columns = [f"κp.{year}" for year in _pv.columns]

        _pv["Datetime"] = pd.to_datetime(
            _pv.index, format="%Y-" + MONTHTIME_FORMAT, errors="coerce"
        )
        _pv = _pv.reset_index(drop=True)
        _pv = _pv.dropna(subset=["Datetime"])

        self.pv = _pv
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
        file_name: str = settings.profile_data.load_profile_file,
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
        _df["Datetime"] = pd.to_datetime(
            _df["Datetime"], format="%Y-" + MONTHTIME_FORMAT, errors="coerce"
        )
        _df = _df.dropna(subset=["Datetime"])

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
        self.pv.set_index("Datetime", inplace=True)
        self.load.set_index("Datetime", inplace=True)
        self.pv = self.pv.resample("15min").interpolate()
        self.load = self.load.resample("15min").interpolate()
        self.pv = self.pv.drop(columns="Datetime", errors="ignore")
        self.load = self.load.drop(columns="Datetime", errors="ignore")
        average_load_p = self.load[
            [c for c in self.load.columns if c.startswith("κp")]
        ].apply(lambda x: x.mean(), axis=1)
        average_load_q = self.load[
            [c for c in self.load.columns if c.startswith("κq")]
        ].apply(lambda x: x.mean(), axis=1)
        average_pv_p = self.pv[
            [c for c in self.pv.columns if c.startswith("κp")]
        ].apply(lambda x: x.mean(), axis=1)
        for c in self.pv.columns:
            if self.pv[c].isnull().any():
                self.pv.loc[self.pv[c].isnull(), c] = average_pv_p.loc[
                    self.pv[c].isnull()
                ]
        for c in self.load.columns:
            if self.load[c].isnull().any():
                if c.startswith("κp"):
                    self.load.loc[self.load[c].isnull(), c] = average_load_p.loc[
                        self.load[c].isnull()
                    ]
                elif c.startswith("κq"):
                    self.load.loc[self.load[c].isnull(), c] = average_load_q.loc[
                        self.load[c].isnull()
                    ]

    def _record_profiles(self):
        """Record the processed profiles to CSV files"""
        pv_output_path = (
            self.INPUT_DATA_DIR / settings.profile_data.processed_pv_profile_file
        )
        real_load_output_path = (
            self.INPUT_DATA_DIR / settings.profile_data.processed_real_load_profile_file
        )
        reactive_load_output_path = (
            self.INPUT_DATA_DIR
            / settings.profile_data.processed_reactive_load_profile_file
        )
        self.pv.to_parquet(pv_output_path)
        self.load[[c for c in self.load.columns if c.startswith("κp")]].to_parquet(
            real_load_output_path
        )
        self.load[[c for c in self.load.columns if c.startswith("κq")]].to_parquet(
            reactive_load_output_path
        )
        logger.info(f"Saved processed PV profiles to {pv_output_path}")
        logger.info(
            f"Saved processed load profiles to {real_load_output_path} and {reactive_load_output_path}"
        )

    def process_and_record_profiles(self):
        self._pv_profile()
        self._load_profile()
        self._handle_missing_values()
        self._record_profiles()
        return self


if __name__ == "__main__":
    profile_reader = ProfileReader().process_and_record_profiles()
