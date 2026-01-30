from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class VaccineDTO:
    id: str
    category: Optional[str] = None
    is_freeze_stable: Optional[bool] = False
    vvm_type: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None
    full_loss_threshold_high: Optional[float] = None
    q10_value: Optional[float] = None
    ideal_temp: Optional[float] = None
    shelf_life_days: Optional[int] = None
    thaw_start_time: Optional[Any] = None
    thaw_duration_days: Optional[int] = 0
