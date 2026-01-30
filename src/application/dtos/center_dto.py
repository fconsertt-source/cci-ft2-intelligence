from dataclasses import dataclass, field
from typing import List, Any, Optional


@dataclass
class CenterDTO:
    id: str
    name: str
    device_ids: List[str] = field(default_factory=list)
    ft2_entries: List[Any] = field(default_factory=list)
    decision: str = "UNKNOWN"
    vvm_stage: str = "NONE"
    alert_level: Optional[str] = None
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    category_display: Optional[str] = None
    decision_reasons: List[str] = field(default_factory=list)
