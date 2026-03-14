from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class TemperatureReading:
    value: float
    timestamp: datetime
    device_id: str


@dataclass(frozen=True)
class EvaluateColdChainSafetyRequest(BaseDTO):
    center_id: Optional[str] = None
    center_name: Optional[str] = None
    readings: Tuple[TemperatureReading, ...] = field(default_factory=tuple)
    vaccines: Tuple[Any, ...] = field(default_factory=tuple)
    # Configuration passed from profile
    temperature_ranges: dict = field(default_factory=dict)
    decision_thresholds: dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluateColdChainSafetyResponse:
    center_id: str
    decision: str
    vvm_stage: str
    alert_level: Optional[str]
    stability_budget_consumed_pct: float
    thaw_remaining_hours: Optional[float]
    category_display: Optional[str]
    decision_reasons: Tuple[str, ...]

    # Optional: Return stats if needed for reporting
    has_freeze: bool = False
    has_ccm_violation: bool = False

    @classmethod
    def from_context(cls, ctx, stats: dict):
        return cls(
            center_id=ctx.id,
            decision=ctx.decision,
            vvm_stage=ctx.vvm_stage,
            alert_level=ctx.alert_level,
            stability_budget_consumed_pct=ctx.stability_budget_consumed_pct,
            thaw_remaining_hours=ctx.thaw_remaining_hours,
            category_display=ctx.category_display,
            decision_reasons=tuple(ctx.decision_reasons),
            has_freeze=stats.get("has_freeze", False),
            has_ccm_violation=stats.get("has_ccm_violation", False),
        )
