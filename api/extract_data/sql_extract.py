import pandas as pd
import sqlalchemy
from common.setup_log import setup_logger
from pathlib import Path
from config import settings

logger = setup_logger(__name__)


class HEIGVDCHMeteoDB:

    def __init__(self, engine: sqlalchemy.engine.base.Engine):
        self.engine = engine
        self.CURRENT_DIR = Path(__file__).parent.parent.parent

    def _query(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.engine)

    def _record_into_parquet(self, df: pd.DataFrame, filename: str):

        df.to_parquet(self.CURRENT_DIR / filename, index=False)

    def _pv_profile_query(self, year: int) -> str:
        return f"""
        SELECT 
        di.`Date and Time` as `Datetime`,
        `Labo Reine.ABB.Power AC [W]` as `PV`
        FROM db_iese_{year} di 
        ORDER BY `Date and Time` DESC
        """

    def extract_pv_profiles(
        self,
        filename: str | None = None,
    ):
        if filename is None:
            filename = (
                settings.profile_data.folder_path
                + "/"
                + settings.profile_data.pv_profile_file
            )
        dfs = []
        for year in range(2020, 2026):
            query_pvs = self._pv_profile_query(year)
            dfs.append(self._query(query_pvs))
            logger.info(f"Extracted PV data for year {year}")

        df = pd.concat(dfs).sort_values(by="Datetime").reset_index(drop=True)
        self._record_into_parquet(df, filename)
        logger.info(f"Saved PV profiles to {filename}")

    def _load_profile_query(self) -> str:
        return f"""
        SELECT 
        rh.`Date et Heure` as `Datetime`,
        `Bleu.P.L1.Moy` as `Blue.P1.Avg`,
        `Bleu.P.L2.Moy` as `Blue.P2.Avg`,
        `Bleu.P.L3.Moy` as `Blue.P3.Avg`,
        `Bleu.P.L1.Min` as `Blue.P1.Min`,
        `Bleu.P.L2.Min` as `Blue.P2.Min`,
        `Bleu.P.L3.Min` as `Blue.P3.Min`,
        `Bleu.P.L1.Max` as `Blue.P1.Max`,
        `Bleu.P.L2.Max` as `Blue.P2.Max`,
        `Bleu.P.L3.Max` as `Blue.P3.Max`,
        `Bleu.Q.L1.Moy` as `Blue.Q1.Avg`,
        `Bleu.Q.L2.Moy` as `Blue.Q2.Avg`,
        `Bleu.Q.L3.Moy` as `Blue.Q3.Avg`,
        `Bleu.Q.L1.Min` as `Blue.Q1.Min`,
        `Bleu.Q.L2.Min` as `Blue.Q2.Min`,
        `Bleu.Q.L3.Min` as `Blue.Q3.Min`,
        `Bleu.Q.L1.Max` as `Blue.Q1.Max`,
        `Bleu.Q.L2.Max` as `Blue.Q2.Max`,
        `Bleu.Q.L3.Max` as `Blue.Q3.Max`,
        `Rouge.P.L1.Moy` as `Red.P1.Avg`,
        `Rouge.P.L2.Moy` as `Red.P2.Avg`,
        `Rouge.P.L3.Moy` as `Red.P3.Avg`,
        `Rouge.P.L1.Min` as `Red.P1.Min`,
        `Rouge.P.L2.Min` as `Red.P2.Min`,
        `Rouge.P.L3.Min` as `Red.P3.Min`,
        `Rouge.P.L1.Max` as `Red.P1.Max`,
        `Rouge.P.L2.Max` as `Red.P2.Max`,
        `Rouge.P.L3.Max` as `Red.P3.Max`,
        `Rouge.Q.L1.Moy` as `Red.Q1.Avg`,
        `Rouge.Q.L2.Moy` as `Red.Q2.Avg`,
        `Rouge.Q.L3.Moy` as `Red.Q3.Avg`,
        `Rouge.Q.L1.Min` as `Red.Q1.Min`,
        `Rouge.Q.L2.Min` as `Red.Q2.Min`,
        `Rouge.Q.L3.Min` as `Red.Q3.Min`,
        `Rouge.Q.L1.Max` as `Red.Q1.Max`,
        `Rouge.Q.L2.Max` as `Red.Q2.Max`,
        `Rouge.Q.L3.Max` as `Red.Q3.Max`
        FROM Reseau_HEIG rh 
        ORDER BY `Date et Heure` DESC
        """

    def extract_load_profiles(
        self,
        filename: str | None = None,
    ):
        if filename is None:
            filename = (
                settings.profile_data.folder_path
                + "/"
                + settings.profile_data.load_profile_file
            )
        query_load = self._load_profile_query()
        df = self._query(query_load).sort_values(by="Datetime").reset_index(drop=True)
        logger.info(f"Extracted load profile data")
        self._record_into_parquet(df, filename)
        logger.info(f"Saved load profiles to {filename}")


if __name__ == "__main__":

    ENGINE = sqlalchemy.create_engine(settings.power_profile_school_sql_url)
    HEIGVDCHMeteoDB(ENGINE).extract_pv_profiles()
    HEIGVDCHMeteoDB(ENGINE).extract_load_profiles()
