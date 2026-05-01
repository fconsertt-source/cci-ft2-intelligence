from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HeatExposure:
    """Heat exposure during a single cold chain stage."""

    stage: str  # "WAREHOUSE", "CLINIC", "VACCINATION_POINT"
    device_id: str
    her: float
    ccm: float
    timestamp: datetime
