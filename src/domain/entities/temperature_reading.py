from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TemperatureReading:
    """
    قراءة درجة حرارة واحدة من جهاز FT2
    """
    vaccine_id: str
    value: float
    recorded_at: datetime
