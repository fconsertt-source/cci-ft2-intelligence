from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TemperatureEntry:
    temperature: float
    timestamp: datetime
    duration_minutes: float
    device_id: str = "UNKNOWN"

    @property
    def value(self) -> float:
        """Compatibility alias → .temperature"""
        return self.temperature

    @property
    def recorded_at(self) -> datetime:
        """Compatibility alias → .timestamp"""
        return self.timestamp
