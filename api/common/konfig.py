import os

SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"
MAX_CPU_COUNT = 32
MAX_ITERATION = 100
SMALL_NUMBER = 1e-5
TIME_RESOLUTION = 1
NOMINAL_FREQUENCY = 50.0
H_SYSTEM = 5.0  # System inertia constant in seconds
NOMINAL_POWER = 100.0  # in kW
DROOP_STORAGE_PF = 0.05  # 5% droop for storage devices
DROOP_STORAGE_QV = 0.05  # 5% droop for storage devices
DROOP_PV_PF = 0.05  # 5% droop for PV systems
OUTPUT_FOLDER = os.path.join(
    os.environ.get("DSS_EXPORT_FOLDER", ""), f"powerflow_results"
)
