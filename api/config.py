from dataclasses import dataclass
from pathlib import Path
from typing import cast
from dynaconf import Dynaconf


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
    power_profile_school_sql_url: str
    profile_data: ProfileDataSettings


settings_not_casted = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=[".secrets.toml", ".settings.toml"],
    root_path=Path(__file__).parent,
)

settings = cast(
    Settings,
    settings_not_casted,
)
