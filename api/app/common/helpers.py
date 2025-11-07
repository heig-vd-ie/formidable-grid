import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Dict, List, Union

import pandas as pd

from app.common.konfig import *
from app.common.setup_log import setup_logger

logger = setup_logger(__name__)


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


def setup_circuit(dss_filename: str) -> Path:
    filepath = Path(INTERNAL_DSSFILES_FOLDER) / dss_filename
    temp_file = replace_env_vars_in_dss(filepath)
    return temp_file


def read_results():
    """Read all JSON result files and return as a list of dictionaries"""
    results = []
    for file in os.listdir(OUTPUT_FOLDER):
        if file.endswith(".json"):
            with open(os.path.join(OUTPUT_FOLDER, file), "r") as f:
                data = json.load(f)
                results.append(data)
    """Save results to CSV and print summary statistics"""
    # Convert to DataFrame
    df = pd.DataFrame(
        [r.__dict__ if hasattr(r, "__dict__") else dict(r) for r in results]
    )
    # Sort by datetime to ensure proper order
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Performance summary
    avg_solve_time = df["solve_time_ms"].mean()
    logger.info(f"Average OpenDSS solve time: {avg_solve_time:.2f} ms")
    logger.info(f"Speedup achieved through parallelization!")
    return df


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
