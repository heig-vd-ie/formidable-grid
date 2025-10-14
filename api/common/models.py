from pydantic import BaseModel


class RunDailyExampleRequest(BaseModel):
    number_of_pvs: int = 5
    pv_capacity_kva_mean: float = 10.0
    storage_capacity_kw_mean: float = 20.0
    grid_forming_percent: float = 0.5
    seed_number: int = 42
