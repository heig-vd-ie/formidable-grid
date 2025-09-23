from unittest.mock import Base

from pydantic import BaseModel


class PowerFlow(BaseModel):
    real_power_kW: float = float("nan")
    reactive_power_kVAr: float = float("nan")


class SimulationResult(BaseModel):
    curr_datetime: str  # ISO 8601 format
    converged: bool
    solve_time_ms: float
    total_power: PowerFlow
    losses: PowerFlow
    bus_voltages: dict[str, float]
    pv_powers: dict[str, PowerFlow]
    storage_powers: dict[str, PowerFlow]
    frequency: float | None = None


def tuple_to_powerflow(power_tuple: tuple[float, float]) -> PowerFlow:
    """Convert a tuple of (real_power_kW, reactive_power_kVAr) to a PowerFlow object."""
    if len(power_tuple) < 1:
        return PowerFlow(real_power_kW=None, reactive_power_kVAr=None)
    elif len(power_tuple) < 2:
        return PowerFlow(real_power_kW=power_tuple[0], reactive_power_kVAr=None)
    return PowerFlow(real_power_kW=power_tuple[0], reactive_power_kVAr=power_tuple[1])
