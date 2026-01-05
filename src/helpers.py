import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Dict, List, Union
from konfig import *
from setup_log import setup_logger

logger = setup_logger(__name__)


def tuple_to_powerflow(power_tuple: list[float]) -> list[float]:
    """Convert a tuple of (real_power_kW, reactive_power_kVAr) to a PowerFlow object."""
    return [
        power_tuple[0],
        power_tuple[2],
        power_tuple[4],
        power_tuple[1],
        power_tuple[3],
        power_tuple[5],
    ]


def threephase_tuple_to_pq(power_tuple: list[float]) -> tuple[float, float]:
    return sum(power_tuple[::2]), sum(power_tuple[1::2])


def clean_nans(obj: Union[Dict, List, float]) -> Union[Dict, List, float, None]:
    """Recursively replace NaN/Inf with None in nested lists/dicts."""
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        else:
            return obj
    else:
        return obj


def setup_env_vars(env_vars: dict):
    for key, value in env_vars.items():
        os.environ[key] = value


def remove_json_files():
    """Remove all JSON files from the output directory"""
    for filename in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete {file_path}. Reason: {e}")


def replace_env_vars_in_dss(dss_file_path: Path) -> Path:
    """
    Reads a DSS file, substitutes environment variables in its content,
    and returns the modified script as a string.
    """
    if not os.path.isfile(dss_file_path):
        raise FileNotFoundError(f"DSS file not found: {dss_file_path}")
    # Read the content of the DSS file
    with open(dss_file_path, "r") as f:
        dss_script_content = f.read()

    substituted_script = os.path.expandvars(dss_script_content)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".dss")
    temp_dss_file_path = temp_file.name

    with open(temp_dss_file_path, "w") as temp_dss_file:
        temp_dss_file.write(substituted_script)
    return Path(temp_dss_file_path)


def initialize_dirs():
    """Initialize working directories & env vars"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.chdir(CURRENT_DIR)


def setup_opendss_file(dss_filename: str) -> Path:
    filepath = Path(INTERNAL_DSSFILES_FOLDER) / dss_filename
    temp_file = replace_env_vars_in_dss(filepath)
    return temp_file


def to_seconds(time_str) -> int:
    # Match number + unit (s, m, h)
    match = re.fullmatch(r"(\d+)([smh])", time_str)
    if not match:
        raise ValueError("Invalid time format")

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    else:
        raise ValueError("Invalid time format")
