from pydantic import BaseModel


class RunDailyExampleRequest(BaseModel):
    number_of_pvs: int = 5
    pv_kva: float = 10.0
    storage_kva: float = 20.0
    gfmi_percentage: float = 0.5
    seed_number: int = 42
