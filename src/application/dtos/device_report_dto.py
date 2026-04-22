# src/application/dtos/device_report_dto.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .reading_dto import ReadingDTO
from .thermal_excursion_dto import ThermalExcursionDTO


class ReportDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_HEAT_C = "REJECTED_HEAT_C"
    REJECTED_FREEZE = "REJECTED_FREEZE"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"
    REJECTED_THAW = "REJECTED_THAW"
    PARTIAL = "PARTIAL"
    SAFE = "SAFE"
    UNKNOWN = "UNKNOWN"


class VVMStage(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass(frozen=True)
class DeviceReportDTO:
    """Immutable DTO for device report data."""
    device_id: str
    center_id: str
    center_name: str
    temperature_ranges: Dict[str, float]
    decision: ReportDecision
    vvm_stage: VVMStage
    alert_level: str = ""
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: float = 0.0
    aefi_reporting_required: bool = False
    flexible_vvm_policy_applied: bool = False
    remaining_shelf_life_ok: bool = True
    decision_reasons: List[str] = field(default_factory=list)
    readings: List[ReadingDTO] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    # Legacy fields for backward compatibility
    vaccine_type: str = ""
    total_records: int = 0
    excursions: List[ThermalExcursionDTO] = field(default_factory=list)
    final_status: str = ""
    scientific_rationale: str = ""
    advisory_section: Dict[str, Any] = field(default_factory=dict)
    validation_required: Optional[Any] = None
    operator: str = ""
    cycle_id: str = ""
    ledger_hash: str = ""

    def get_batch_counts(self) -> Dict[str, int]:
        """Count excursions by impact level for batch reporting."""
        counts = {"safe": 0, "warning": 0, "discard": 0}
        for excursion in self.excursions:
            impact = excursion.impact_level.lower()
            if impact == "safe":
                counts["safe"] += 1
            elif impact == "partial":
                counts["warning"] += 1
            elif impact == "discard":
                counts["discard"] += 1
        return counts

    def __post_init__(self):
        # تحويل readings من dict إلى ReadingDTO
        if self.readings:
            converted = []
            for r in self.readings:
                if isinstance(r, dict):
                    from src.application.dtos.reading_dto import ReadingDTO
                    converted.append(ReadingDTO.from_dict(r))
                else:
                    converted.append(r)
            object.__setattr__(self, 'readings', converted)
        if not self.device_id:
            raise ValueError("device_id cannot be empty")
        if not self.center_id:
            raise ValueError("center_id cannot be empty")
        if self.stability_budget_consumed_pct < 0 or self.stability_budget_consumed_pct > 100:
            raise ValueError("stability_budget_consumed_pct must be between 0 and 100")
        if not isinstance(self.decision, ReportDecision):
            raise ValueError(f"Invalid decision: {self.decision}")
        if not isinstance(self.vvm_stage, VVMStage):
            raise ValueError(f"Invalid VVM stage: {self.vvm_stage}")
        if 'min' in self.temperature_ranges and 'max' in self.temperature_ranges:
            if self.temperature_ranges['min'] > self.temperature_ranges['max']:
                raise ValueError("Minimum temperature cannot be greater than maximum temperature in temperature_ranges")
    @classmethod
    def create_golden_baseline(cls) -> "DeviceReportDTO":
        """Factory method للـ Golden Baseline – يعمل مع الـ enums المحلية"""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        return cls(
            device_id="GOLDEN-TEST-001",
            center_id="CENTER-GOLDEN-001",
            center_name="مركز الاختبار الذهبي (Golden Test Center)",
            temperature_ranges={"min": 2.0, "max": 8.0},
            decision=ReportDecision.SAFE,           # استخدام الـ Enum المحلي
            vvm_stage=VVMStage.B,                   # B موجود في الـ Enum الحالي
            vaccine_type="Pfizer-BioNTech",
            total_records=100,
            excursions=[],
            final_status="safe",
            scientific_rationale="Golden baseline validation for all PDF strategies",
            generated_at=datetime.now(ZoneInfo("UTC")).isoformat(),
            decision_reasons=["جميع القراءات ضمن النطاق المسموح – Golden Baseline"],
            readings=[],
            stats={},
            alert_level="",
            stability_budget_consumed_pct=0.0,
            thaw_remaining_hours=0.0,
        )