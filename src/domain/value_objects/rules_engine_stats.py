from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RulesEngineStats:
    max_temp: float = 0.0
    min_temp: float = 0.0
    avg_temp: float = 0.0

    freeze_duration: float = 0.0
    heat_duration: float = 0.0

    has_freeze: bool = False
    has_ccm_violation: bool = False

    her: float = 0.0

    metadata: dict[str, any] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "RulesEngineStats":
        """
        Adapter to ensure backward compatibility during migration.
        """

        return cls(
            max_temp=data.get("max_temp", 0.0),
            min_temp=data.get("min_temp", 0.0),
            avg_temp=data.get("avg_temp", 0.0),
            freeze_duration=data.get("freeze_duration", 0.0),
            has_freeze=data.get("has_freeze", False),
            metadata=data,
        )

    def to_dict(self) -> dict:
        """
        Backward compatibility layer (temporary).
        """

        return {
            "max_temp": self.max_temp,
            "min_temp": self.min_temp,
            "avg_temp": self.avg_temp,
            "freeze_duration": self.freeze_duration,
            "has_freeze": self.has_freeze,
        }
