# src/application/dtos/thermal_excursion_dto.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ThermalExcursionDTO:
    """تفاصيل التعرض الحراري (خارج النطاق المسموح)"""
    device_id: str
    excursion_type: str  # 'HEAT' or 'FREEZE'
    duration_minutes: float
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    timestamp: Optional[str] = None
    impact_level: str = "UNKNOWN"

    def __post_init__(self):
        """التحقق من صحة البيانات الأساسية"""
        if not self.device_id:
            raise ValueError("device_id cannot be empty")
        if self.excursion_type not in ('HEAT', 'FREEZE'):
            raise ValueError(f"Invalid excursion_type: {self.excursion_type}")
        if self.duration_minutes < 0:
            raise ValueError("duration_minutes cannot be negative")