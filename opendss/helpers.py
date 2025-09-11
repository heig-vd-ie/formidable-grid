import os
import tempfile


def replace_env_vars_in_dss(dss_file_path: str) -> str:
    """
    Reads a DSS file, substitutes environment variables in its content,
    and returns the modified script as a string.
    """
    if not os.path.isfile(dss_file_path):
        raise FileNotFoundError(f"DSS file not found: {dss_file_path}")
    # Read the content of the DSS file
    with open(dss_file_path, "r") as f:
        dss_script_content = f.read()
    # Substitute the environment variables
    # os.path.expandvars will replace $EXTERNAL_DSSFILES_FOLDER and $INTERNAL_DSSFILES_FOLDER
    # with the values from your environment (e.g., from .envrc)
    substituted_script = os.path.expandvars(dss_script_content)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".dss")
    temp_dss_file_path = temp_file.name

    with open(temp_dss_file_path, "w") as temp_dss_file:
        temp_dss_file.write(substituted_script)
    return temp_dss_file_path
