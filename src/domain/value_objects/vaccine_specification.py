from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class VaccineSpecification:
    vaccine_type: str
    min_temp: float
    max_temp: float
    freeze_sensitive: bool
    rationale: str = ""

    # الحقول الإضافية اللازمة للقرار التنظيمي
    freeze_range: Optional[List[float]] = None           
    max_heat_temp: Optional[float] = None               
    max_heat_duration_hours: Optional[float] = None    
    regulatory_source: str = "WHO/IVB/06.10"          
    excursion_time_limit: Optional[float] = None       # ← للتوافق مع الملفات الحالية
