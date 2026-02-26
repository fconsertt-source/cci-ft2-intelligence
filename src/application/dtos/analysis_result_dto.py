# src/application/dtos/analysis_result_dto.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum
from src.domain.enums.vvm_stage import VVMStage

class VaccineStatus(Enum):
    SAFE = "SAFE"
    PARTIAL = "PARTIAL"
    DISCARD = "DISCARD"

@dataclass(frozen=True)  # ← immutability enforced
class AnalysisResultDTO:
    vaccine_id: str
    status: VaccineStatus
    her: float
    ccm: float
    vvm_stage: VVMStage = VVMStage.NONE
    alert_level: str = "GREEN"
    category_display: str = ""
    thaw_remaining_hours: Optional[float] = None
    is_thawing: bool = False
    stability_budget_consumed_pct: float = 0.0
    
    # ⚠️ التغيير الجوهري: جميع الحقول غير قابلة للتغيير
    decision_reasons: Tuple[str, ...] = ()
    audit_log: Tuple[dict, ...] = ()
    recommendations: Tuple[str, ...] = ()
    # ❌ تم إزالة: add_reason(), generate_recommendations()