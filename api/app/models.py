import numpy as np
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
