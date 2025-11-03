from app.dss_worker import DSSWorker, read_results, run_daily_powerflow
from app.helpers import setup_and_run_circuit, setup_circuit
from app.plotter import create_qsts_plots, plot_grid_topology, plot_monitor_results
from extract_data.profile_reader import ProfileReader
from extract_data.sql_extract import HEIGVDCHMeteoDB
from config import settings
import sqlalchemy


def _recreate_profile_data():
    ENGINE = sqlalchemy.create_engine(settings.power_profile_school_sql_url)
    HEIGVDCHMeteoDB(ENGINE).extract_pv_profiles()
    HEIGVDCHMeteoDB(ENGINE).extract_load_profiles()
    ProfileReader().process_and_record_profiles()


__all__ = [
    "create_qsts_plots",
    "setup_circuit",
    "ProfileReader",
    "HEIGVDCHMeteoDB",
    "settings",
    "read_results",
    "DSSWorker",
    "setup_and_run_circuit",
    "plot_grid_topology",
    "plot_monitor_results",
    "run_daily_powerflow",
    "_recreate_profile_data",
]
