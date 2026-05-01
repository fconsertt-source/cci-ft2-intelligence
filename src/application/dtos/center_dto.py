from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class CenterDTO:
    id: str
    name: str
    equipment: Dict[str, Any] = field(default_factory=dict)
    temperature_ranges: Dict[str, float] = field(default_factory=dict)
    decision_thresholds: Dict[str, Any] = field(default_factory=dict)
    equipment_units: List[Any] = field(default_factory=list)
    device_ids: List[str] = field(default_factory=list)
    ft2_entries: List[Any] = field(default_factory=list)
    decision: str = "UNKNOWN"
    has_warning: bool = False
    vvm_stage: str = "NONE"
    alert_level: Optional[str] = None
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    category_display: Optional[str] = None
    decision_reasons: List[str] = field(default_factory=list)
    
