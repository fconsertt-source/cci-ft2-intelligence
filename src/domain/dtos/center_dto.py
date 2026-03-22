# src/domain/dtos/center_dto.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def ft2_entries_count(self) -> int:
        return len(self.ft2_entries)

    @property
    def has_warning(self) -> bool:
        return self.alert_level is not None and self.alert_level.upper() not in [
            "NONE",
            "SAFE",
            "",
        ]

    @property
    def has_error(self) -> bool:
        return self.decision.upper() in ["CRITICAL", "UNSAFE", "REJECT"]

    @property
    def has_freeze(self) -> bool:
        return self.stats.get("has_freeze", False)

    @property
    def has_ccm_violation(self) -> bool:
        return self.stats.get("has_ccm_violation", False)

    @property
    def her_ratio(self) -> float:
        return float(self.stats.get("her_ratio", 0.0))

    @property
    def ccm_index(self) -> str:
        return str(self.stats.get("ccm_index", "0"))

    @property
    def judgment_risk(self) -> str:
        return self.stats.get("judgment_risk", "SAFE")

    @property
    def judgment_narrative(self) -> str:
        return self.stats.get("judgment_narrative", "")

    @property
    def judgment_icon(self) -> str:
        return self.stats.get("judgment_icon", "🟢")

    @property
    def confidence(self) -> float:
        return float(self.stats.get("confidence", 0.0))

    @property
    def requires_review(self) -> bool:
        return self.stats.get("requires_review", False)

    @property
    def her_percentage(self) -> float:
        return float(self.stats.get("her_percentage", 0.0))

    @property
    def avg_temperature(self) -> str:
        avg = self.stats.get("avg_temp")
        return f"{avg:.2f}" if avg is not None else "N/A"

    @property
    def min_temperature(self) -> str:
        min_t = self.stats.get("min_temp")
        return f"{min_t:.2f}" if min_t is not None else "N/A"

    @property
    def max_temperature(self) -> str:
        max_t = self.stats.get("max_temp")
        return f"{max_t:.2f}" if max_t is not None else "N/A"
