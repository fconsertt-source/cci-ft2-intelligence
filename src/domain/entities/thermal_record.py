from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThermalRecord:
    """
    Domain entity representing a thermal measurement event.

    Identity principle: A thermal record cannot exist without
    belonging to a specific physical device — device_id is intrinsic identity.
    """

    device_id: str
    timestamp: datetime
    temperature: float
    duration_minutes: float
    vaccine_type: str
