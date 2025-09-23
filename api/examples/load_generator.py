# %%
from pylpg import lpg_execution, lpgdata

# Simulate the predefined household CHR01 (couple, both employed) for the year 2025
data = lpg_execution.execute_lpg_single_household(
    year=2022,
    householdref=lpgdata.Households.CHR01_Couple_both_at_Work,
    housetype=lpgdata.HouseTypes.HT20_Single_Family_House_no_heating_cooling,
    startdate="2022-01-01",
    enddate="2022-01-02",
    resolution="00:01:00",
    random_seed=42,
)

electricity_profile = data["Electricity_HH1"]
