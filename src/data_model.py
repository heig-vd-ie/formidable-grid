from dataclasses import dataclass
import pandas as pd
from pydantic import BaseModel


class PowerFlowResponse(BaseModel):
    bus_names: list[str]
    powers: list[float]
    voltages: list[float]
    currents: list[float]


class SimulationResponse(BaseModel):
    timesteps: str  # ISO 8601 format, comma-separated
    solve_times_ms: float
    converged: bool
    frequency: float
    voltages: dict[str, list[float]]
    lines: dict[str, PowerFlowResponse]
    loads: dict[str, PowerFlowResponse]
    generators: dict[str, PowerFlowResponse]
    storages: dict[str, PowerFlowResponse]
    pvsystems: dict[str, PowerFlowResponse]
    vsources: dict[str, PowerFlowResponse]


class GfmKace(BaseModel):
    number_of_pvs: int = 5
    pv_kva: float = 10.0
    storage_kva: float = 20.0
    gfmi_percentage: float = 0.5
    seed_number: int = 42


@dataclass
class ProfileData:
    pv: pd.DataFrame
    load_p: pd.DataFrame
    load_q: pd.DataFrame


class SetPoints(BaseModel):
    p: dict[str, float]
    q: dict[str, float]


class ElementsSetPoints(BaseModel):
    load: SetPoints
    pvsystem: SetPoints
    storage: SetPoints


class FreqCoefficients(BaseModel):
    droop: dict[str, float]
    damping: float
