import os
from opendssdirect import dss

filepath = os.path.join(
    os.path.dirname(__file__),
    "DSSfiles",
    "GFL_IEEE123",
    "Run_IEEE123Bus_GFLDaily_DynExp.dss",
)
print(f"Running OpenDSS file: {filepath}")
dss.run_command("Clear")
dss.run_command(f'Redirect "{filepath}"')
