# src.domain.entities.temperature_reading.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TemperatureReading:
    """
    قراءة درجة حرارة للقاح في وقت محدد.
    
    Reference: WHO/IVB/06.10 — Temperature monitoring requirements
    """
    vaccine_id: str
    value: float  # درجة الحرارة بالسلسيوس
    recorded_at: datetime
    duration_hours: Optional[float] = None  # مدة القراءة (اختياري)
    device_id: Optional[str] = None  # معرف جهاز المراقبة
    location: Optional[str] = None  # موقع القراءة
    
    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"value يجب أن يكون رقمياً: {self.value}")
        if not isinstance(self.recorded_at, datetime):
            raise ValueError(f"recorded_at يجب أن يكون datetime: {self.recorded_at}")