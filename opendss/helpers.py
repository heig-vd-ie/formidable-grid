import os
from pathlib import Path
import tempfile
from opendssdirect import dss


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


def setup_circuit(dss_filename: str):
    filepath = Path(os.getenv("INTERNAL_DSSFILES_FOLDER", "")) / dss_filename

    temp_file = replace_env_vars_in_dss(filepath)

    dss.Command("Clear")
    dss.Command(f'Redirect "{temp_file}"')

    os.remove(temp_file)
    print(f"Temp file {temp_file} removed.")
    return dss
