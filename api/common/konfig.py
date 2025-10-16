import os

SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"
MAX_CPU_COUNT = 32
MAX_ITERATION = 1
SMALL_NUMBER = 1e-5
NOMINAL_DROOP = 0.1
NOMINAL_DAMPING = 1.0
NOMINAL_FREQUENCY = 50.0
OUTPUT_FOLDER = os.path.join(
    os.environ.get("DSS_EXPORT_FOLDER", ""), f"powerflow_results"
)
