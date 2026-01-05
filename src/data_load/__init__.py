import sqlalchemy
from konfig import settings
from data_load.profile_reader import ProfileReader
from data_load.sql_extract import HEIGVDCHMeteoDB


def _recreate_profile_data():
    ENGINE = sqlalchemy.create_engine(settings.power_profile_school_sql_url)
    HEIGVDCHMeteoDB(ENGINE).extract_pv_profiles()
    HEIGVDCHMeteoDB(ENGINE).extract_load_profiles()
    ProfileReader().process_and_record_profiles()


__all__ = [
    "ProfileReader",
    "HEIGVDCHMeteoDB",
    "settings",
    "_recreate_profile_data",
]
