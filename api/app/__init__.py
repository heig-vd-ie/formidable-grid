import sqlalchemy

from app.common.konfig import settings
from app.common.models import ExtraUnitRequest
from app.dss_worker.power_flow import run_qsts_powerflow
from app.dss_worker.ray_handler import ray_init, ray_shutdown
from app.extract_data.profile_reader import ProfileReader
from app.extract_data.sql_extract import HEIGVDCHMeteoDB
from app.common.helpers import read_results
from app.common.plotter import create_qsts_plots


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
    "run_qsts_powerflow",
    "_recreate_profile_data",
]
