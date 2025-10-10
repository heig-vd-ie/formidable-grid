import pandas as pd
import sqlalchemy
from common.setup_log import setup_logger

logger = setup_logger(__name__)


class HEIGVDCHMeteoDB:
    def __init__(self, engine: sqlalchemy.engine.base.Engine):
        self.engine = engine

    def _query(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.engine)

    def _record_into_parquet(self, df: pd.DataFrame, filename: str):
        df.to_parquet(filename, index=False)

    def extract_pv_profiles(self, filename: str):
        dfs = []
        for year in range(2020, 2025):
            QUERY_PVs = f"""
            SELECT 
            di.`Date and Time` as `Datetime`,
            `Labo Reine.SolarMax.Power AC [W]` as `PV1`, 
            `Labo Reine.ABB.Power AC [W]` as `PV2`,
            `Labo Reine.Kaco.Power AC [W]` as `PV3` 
            FROM db_iese_{year} di 
            ORDER BY `Date and Time` DESC
            """

            dfs.append(self._query(QUERY_PVs))
            logger.info(f"Extracted PV data for year {year}")

        df = pd.concat(dfs).sort_values(by="Datetime").reset_index(drop=True)
        self._record_into_parquet(df, filename)
        logger.info(f"Saved PV profiles to {filename}")


if __name__ == "__main__":
    from config import settings

    ENGINE = sqlalchemy.create_engine(settings.power_profile_school_sql_url)
    HEIGVDCHMeteoDB(ENGINE).extract_pv_profiles("data/inputs/pv_profiles.parquet")
