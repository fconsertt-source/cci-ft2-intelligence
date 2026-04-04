from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CenterStatsDTO:
    """حاوية إحصائيات المركز الفيزيائية (avg, min, max, etc)"""
    center_id: str
    num_ft2_entries: int
    has_freeze: bool
    has_ccm_violation: bool
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None