# src/domain/enums/vaccine_decision.py
"""
VaccineDecision + DecisionReason — قرارات تقييم اللقاح وأسبابها.
"""
from __future__ import annotations

from enum import Enum


class VaccineDecision(Enum):
    """القرار النهائي على دفعة لقاح."""

    SAFE = "safe"
    PARTIAL = "partial"
    DISCARD = "discard"
    EXPIRED = "expired"


class DecisionReason(Enum):
    """سبب القرار — يُستخدم في التقارير وسجل التدقيق."""

    WITHIN_LIMITS = "within_limits"  # HER ≤ 1.0 — ضمن الحدود
    PARTIAL_EXPOSURE = "partial_exposure"  # 1.0 < HER ≤ 1.5
    HEAT_EXCESS = "heat_excess"  # HER > 1.5
    CCM_BREAK = "ccm_break"  # CCM وصل للنافذة D
    FREEZE_EVENT = "freeze_event"  # تجمد للقاح حساس
    VVM_CRITICAL = "vvm_critical"  # VVM مرحلة 3 أو 4
    EXPIRED = "expired"  # انتهت الصلاحية
