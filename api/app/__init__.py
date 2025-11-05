from extract_data.profile_reader import ProfileReader
from extract_data.sql_extract import HEIGVDCHMeteoDB
from common.konfig import settings

from app.dss_worker import run_daily_powerflow
from app.helpers import read_results
from app.plotter import create_qsts_plots
from app.ray_handler import ray_init, ray_shutdown
from common.models import ExtraUnitRequest

import sqlalchemy


def _recreate_profile_data():
    ENGINE = sqlalchemy.create_engine(settings.power_profile_school_sql_url)
    HEIGVDCHMeteoDB(ENGINE).extract_pv_profiles()
    HEIGVDCHMeteoDB(ENGINE).extract_load_profiles()
    ProfileReader().process_and_record_profiles()


__all__ = [
    "create_qsts_plots",
    "ray_init",
    "ray_shutdown",
    "ProfileReader",
    "HEIGVDCHMeteoDB",
    "settings",
    "read_results",
    "ExtraUnitRequest",
    "run_daily_powerflow",
    "_recreate_profile_data",
]
