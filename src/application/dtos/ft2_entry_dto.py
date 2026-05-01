"""FT2 Entry DTO — Application Layer"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FT2EntryDTO:
    """
    يمثل قراءة واحدة من جهاز FT2.
    يحتوي على جميع الحقول من الملف الخام + حقول محسوبة.
    """
    id: str
    device_id: str
    timestamp: str
    temperature: float
    duration_minutes: int
    vaccine_type: Optional[str] = None
    batch: Optional[str] = None
    center_id: Optional[str] = None
    freeze_duration: int = 0  # ← حرجة لتحليل التجميد
    heat_duration: int = 0    # ← حرجة لتحليل الحرارة
    
    @property
    def is_freeze_risk(self) -> bool:
        """هل هناك خطر تجميد؟"""
        return self.temperature < 0.0 or self.freeze_duration > 0
    
    @property
    def is_heat_risk(self) -> bool:
        """هل هناك خطر حرارة؟"""
        return self.temperature > 8.0 or self.heat_duration > 0
