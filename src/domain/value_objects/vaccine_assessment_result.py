# src/domain/value_objects/vaccine_assessment_result.py
"""
VaccineAssessmentResult — نتيجة تقييم دفعة لقاح واحدة.
Immutable — تُنشأ مرة واحدة ولا تتغير.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.domain.enums.vaccine_decision import DecisionReason, VaccineDecision


@dataclass(frozen=True)
class VaccineAssessmentResult:
    """
    نتيجة تقييم دفعة لقاح واحدة.

    Attributes:
        equipment_id:   معرف المعدة
        entry_id:       معرف سجل اللقاح في equipment_vaccines
        vaccine_type:   نوع اللقاح
        batch_number:   رقم الدفعة
        decision:       القرار النهائي (SAFE/PARTIAL/DISCARD/EXPIRED)
        reason:         سبب القرار
        her_ratio:      نسبة HER المحسوبة
        ccm_index:      مؤشر CCM (0/A/AB/ABC/D)
        decision_detail: تفاصيل نصية للقرار
        evaluated_at:   وقت التقييم
    """

    equipment_id: str
    entry_id: str
    vaccine_type: str
    batch_number: str
    decision: VaccineDecision
    reason: DecisionReason
    her_ratio: float
    ccm_index: str
    decision_detail: str
    evaluated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.evaluated_at is None:
            object.__setattr__(
                self, "evaluated_at", datetime.now(timezone.utc)
            )

    @property
    def is_usable(self) -> bool:
        return self.decision in (VaccineDecision.SAFE, VaccineDecision.PARTIAL)

    def to_dict(self) -> dict:
        return {
            "equipment_id": self.equipment_id,
            "entry_id": self.entry_id,
            "vaccine_type": self.vaccine_type,
            "batch_number": self.batch_number,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "her_ratio": round(self.her_ratio, 6),
            "ccm_index": self.ccm_index,
            "decision_detail": self.decision_detail,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }

    def to_tsv_row(self) -> str:
        """تحويل إلى سطر TSV للتقرير النهائي."""
        return "\t".join([
            self.equipment_id,
            self.vaccine_type,
            self.batch_number,
            self.decision.value.upper(),
            self.reason.value,
            f"{self.her_ratio:.6f}",
            self.ccm_index,
            self.decision_detail,
        ])