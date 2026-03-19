from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RulesEngineStats:
    max_temp: float = 0.0
    min_temp: float = 0.0
    avg_temp: float = 0.0

    freeze_duration: float = 0.0
    heat_duration: float = 0.0

    has_freeze: bool = False
    has_ccm_violation: bool = False

    her: float = 0.0

    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "RulesEngineStats":
        known = {
            "max_temp",
            "min_temp",
            "avg_temp",
            "freeze_duration",
            "heat_duration",
            "has_freeze",
            "has_ccm_violation",
            "her",
        }
        kwargs = {k: data[k] for k in known if k in data}
        return cls(**kwargs, metadata=data)

    def to_dict(self) -> dict:
        return {
            "max_temp": self.max_temp,
            "min_temp": self.min_temp,
            "avg_temp": self.avg_temp,
            "freeze_duration": self.freeze_duration,
            "heat_duration": self.heat_duration,
            "has_freeze": self.has_freeze,
            "has_ccm_violation": self.has_ccm_violation,
            "her": self.her,
        }

    # legacy dict-style access
    def __getitem__(self, key: str):
        return self.to_dict()[key]

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)
