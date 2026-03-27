# src/domain/dtos/evaluate_cold_chain_safety_request.py
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.domain.dtos.base_dto import BaseDTO
from src.domain.value_objects.vaccine_specification import VaccineSpecification


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
    vaccine_inventory: Optional[Dict[str, Any]] = None
    vaccine_spec: Optional[VaccineSpecification] = None
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
    has_freeze: bool = False
    has_ccm_violation: bool = False
    her_ratio: float = 0.0
    ccm_index: str = "0"
    judgment_risk: str = "SAFE"
    judgment_icon: str = "🟢"
    confidence: float = 0.0
    requires_review: bool = False
    her_percentage: float = 0.0
    judgment_narrative: str = ""

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
            her_ratio=stats.get("her_ratio", 0.0),
            ccm_index=stats.get("ccm_index", "0"),
            judgment_risk=stats.get("judgment_risk", "SAFE"),
            judgment_icon=stats.get("judgment_icon", "🟢"),
            confidence=stats.get("confidence", 0.0),
            requires_review=stats.get("requires_review", False),
            her_percentage=stats.get("her_percentage", 0.0),
            judgment_narrative=stats.get("judgment_narrative", ""),
        )
