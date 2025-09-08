import os
from opendssdirect import dss, enums


print("OpenDSSDirect.py and engine versions:", dss.Version())

dss.Basic.ClearAll()
file_path = (
    os.path.dirname(os.path.abspath(__file__))
    + "/../../data/inputs/GFL_IEEE123/Run_IEEE123Bus_GFLDaily_DynExp.dss"
)

os.chdir(os.path.dirname(file_path))
dss.Basic.ClearAll()
dss.Command(f'Redirect "{os.path.abspath(file_path)}"')
