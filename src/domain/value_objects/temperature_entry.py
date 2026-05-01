from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TemperatureEntry:
    temperature: float
    timestamp: datetime
    duration_minutes: float
    device_id: str = "UNKNOWN"
