from dataclasses import dataclass
from pydantic import BaseModel
from pathlib import Path


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


def tuple_to_powerflow(power_tuple: list[float]) -> list[float]:
    """Convert a tuple of (real_power_kW, reactive_power_kVAr) to a PowerFlow object."""
    return [
        power_tuple[0],
        power_tuple[2],
        power_tuple[4],
        power_tuple[1],
        power_tuple[3],
        power_tuple[5],
    ]


class ExtraUnitRequest(BaseModel):
    number_of_pvs: int = 5
    pv_kva: float = 10.0
    storage_kva: float = 20.0
    gfmi_percentage: float = 0.5
    seed_number: int = 42


@dataclass
class InputDSSWorker:
    basedir: str
    temp_file: Path
    env_vars: dict
