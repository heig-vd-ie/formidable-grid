import os
from opendssdirect import dss, enums


print("OpenDSSDirect.py and engine versions:", dss.Version())

dss.Basic.ClearAll()
file_path = (
    os.path.dirname(os.path.abspath(__file__))
    + "/../../data/inputs/European_LV_Test_Feeder-G/Master.dss"
)

os.chdir(os.path.dirname(file_path))
dss.Command(f'Redirect "{os.path.abspath(file_path)}"')
dss.Solution.Mode(enums.SolveModes.Daily)


print(dss.utils.loads_to_dataframe())

print(dss.utils.monitors_to_dataframe())
