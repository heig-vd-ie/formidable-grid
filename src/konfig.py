import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from dynaconf import Dynaconf

SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"
MAX_CPU_COUNT = 32
MAX_ITERATION = 3
SMALL_NUMBER = 1e-5
NOMINAL_DROOP = 0.04
NOMINAL_DAMPING = 0.01
NOMINAL_FREQUENCY = 50.0

NUMBER_OF_PV_SHAPES = 5
STEP_SIZE = "15m"
EXTERNAL_DSSFILES_FOLDER = "/app/artifacts/inputs/ExternalDSSfiles"
INTERNAL_DSSFILES_FOLDER = "/app/artifacts/inputs/InternalDSSfiles"
DSS_EXPORT_FOLDER = "/app/artifacts/outputs"

OUTPUT_FOLDER = Path(DSS_EXPORT_FOLDER) / f"powerflow_results"
CURRENT_DIR = os.getcwd()


@dataclass
class ProfileDataSettings:
    pv_profile_file: str
    load_profile_file: str
    processed_pv_profile_file: str
    processed_real_load_profile_file: str
    processed_reactive_load_profile_file: str
    folder_path: str
    output_folder_path: str


@dataclass
class Settings:
    profile_data: ProfileDataSettings
    power_profile_school_sql_url: str = ""


settings_not_casted = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=[".secrets.toml", ".settings.toml"],
    root_path=Path(__file__).parent,
)

settings = cast(
    Settings,
    settings_not_casted,
)
