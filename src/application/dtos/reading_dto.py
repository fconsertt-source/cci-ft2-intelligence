from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ReadingDTO:
    timestamp: datetime
    temperature: float
    duration: float = 0.0
    device_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ReadingDTO":
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif not isinstance(ts, datetime):
            raise ValueError(f"Invalid timestamp type: {type(ts)}")
        return cls(
            timestamp=ts,
            temperature=float(data["temperature"]),
            duration=float(data.get("duration", 0.0)),
            device_id=data.get("device_id")
        )
