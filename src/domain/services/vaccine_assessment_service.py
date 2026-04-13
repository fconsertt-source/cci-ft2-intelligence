# src/domain/services/vaccine_assessment_service.py
"""
VaccineAssessmentService — محرك قرارات سلامة اللقاحات.

التسلسل الهرمي للقرار (Fail-Fast):
  1. انتهاء الصلاحية     → EXPIRED   (فوري)
  2. VVM مرحلة 3 أو 4    → DISCARD   (فوري)
  3. Circuit Breaker     → DISCARD   (فوري — تجمد أو 34°C)
  4. CCM index D         → DISCARD   (فوري)
  5. HER > 1.5           → DISCARD
  6. HER > 1.0           → PARTIAL
  7. HER ≤ 1.0           → SAFE

مصدر الحقيقة الوحيد للحسابات: ExposureAnalysisService
"""
from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from src.domain.entities.equipment_vaccine import EquipmentVaccine
from src.domain.enums.vaccine_decision import DecisionReason, VaccineDecision
from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.value_objects.vaccine_assessment_result import \
    VaccineAssessmentResult
from src.domain.value_objects.vaccine_specification import (
    HER_PARTIAL_MAX, HER_SAFE_MAX, VaccineSpecification, get_vaccine_spec)

logger = logging.getLogger(__name__)


class VaccineAssessmentService:
    """
    محرك قرارات سلامة اللقاحات.

    يستخدم ExposureAnalysisService كمصدر وحيد للحسابات الحرارية.
    العتبات مستنبطة من vaccine_catalogue (قابلة للتعديل).
    """

    def __init__(
        self,
        exposure_service: Optional[ExposureAnalysisService] = None,
    ) -> None:
        self._exposure = exposure_service or ExposureAnalysisService()

    def assess(
        self,
        vaccine: EquipmentVaccine,
        readings: List,
        spec: Optional[VaccineSpecification] = None,
        reference_date: Optional[date] = None,
    ) -> VaccineAssessmentResult:
        """
        تقييم دفعة لقاح واحدة.

        Args:
            vaccine:        بيانات الدفعة (من EquipmentVaccineRepository)
            readings:       قراءات الحرارة (من FT2)
            spec:           مواصفات اللقاح (اختياري — يُستنبط من vaccine_type)
            reference_date: تاريخ المرجع للتحقق من الصلاحية (افتراضي: اليوم)

        Returns:
            VaccineAssessmentResult — نتيجة غير قابلة للتعديل
        """
        ref_date = reference_date or date.today()

        # جلب المواصفة إن لم تُمرَّر
        if spec is None:
            spec = get_vaccine_spec(vaccine.vaccine_type)

        # ── المستوى 1: انتهاء الصلاحية ───────────────────────
        if ref_date > vaccine.expiry_date:
            days_over = (ref_date - vaccine.expiry_date).days
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.EXPIRED,
                reason=DecisionReason.EXPIRED,
                her_ratio=0.0,
                ccm_index="N/A",
                detail=f"انتهت الصلاحية منذ {days_over} يوم",
            )

        # ── المستوى 2: VVM مرحلة 3 أو 4 ─────────────────────
        if vaccine.has_vvm and vaccine.vvm_stage is not None:
            if not vaccine.vvm_stage.is_usable:
                return self._result(
                    vaccine=vaccine,
                    decision=VaccineDecision.DISCARD,
                    reason=DecisionReason.VVM_CRITICAL,
                    her_ratio=0.0,
                    ccm_index="N/A",
                    detail=(
                        f"VVM وصل {vaccine.vvm_stage.label_ar} — " "تجاوز نقطة الإلغاء"
                    ),
                )

        # ── تحليل التعرض الحراري (Q10 + CCM + Circuit Breakers) ──
        if readings:
            analysis = self._exposure.analyze(readings=readings, spec=spec)
            her_ratio = analysis.her_ratio
            ccm_index = analysis.ccm_index
            circuit_breaker = analysis.circuit_breaker
        else:
            # لا قراءات → نعتمد على VVM فقط
            logger.warning(
                "لا قراءات حرارية للقاح %s/%s — التقييم بدون HER",
                vaccine.vaccine_type,
                vaccine.batch_number,
            )
            her_ratio = 0.0
            ccm_index = "0"
            circuit_breaker = None

        # ── المستوى 3: Circuit Breaker ────────────────────────
        if circuit_breaker == "FREEZE_EXCURSION":
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.DISCARD,
                reason=DecisionReason.FREEZE_EVENT,
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                detail=(
                    f"تجمد مكتشف — لقاح {spec.vaccine_type} "
                    "حساس للتجمد (يحتوي ألومنيوم)"
                ),
            )

        if circuit_breaker == "CRITICAL_HEAT_34C":
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.DISCARD,
                reason=DecisionReason.CCM_BREAK,
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                detail=(
                    f"حرارة حرجة فوق {spec.critical_temp_c:.0f}°C "
                    f"لأكثر من {spec.critical_hours:.0f} ساعات"
                ),
            )

        # ── المستوى 4: CCM Index D ────────────────────────────
        if ccm_index == "D":
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.DISCARD,
                reason=DecisionReason.CCM_BREAK,
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                detail="مؤشر CCM وصل للنافذة D — تعرض حراري حرج",
            )

        # ── المستوى 5 و 6 و 7: HER ratio ─────────────────────
        return self._decide_by_her(
            vaccine=vaccine,
            her_ratio=her_ratio,
            ccm_index=ccm_index,
        )

    def assess_all(
        self,
        vaccines: List[EquipmentVaccine],
        readings: List,
        reference_date: Optional[date] = None,
    ) -> List[VaccineAssessmentResult]:
        """
        تقييم جميع اللقاحات في معدة واحدة.

        Args:
            vaccines:  قائمة اللقاحات في المعدة
            readings:  قراءات الحرارة (مشتركة لجميع اللقاحات)
            reference_date: تاريخ المرجع

        Returns:
            قائمة نتائج مرتبة: DISCARD أولاً ثم PARTIAL ثم SAFE
        """
        results = [
            self.assess(vaccine, readings, reference_date=reference_date)
            for vaccine in vaccines
        ]

        # ترتيب: DISCARD/EXPIRED أولاً
        priority = {
            VaccineDecision.DISCARD: 0,
            VaccineDecision.EXPIRED: 1,
            VaccineDecision.PARTIAL: 2,
            VaccineDecision.SAFE: 3,
        }
        return sorted(results, key=lambda r: priority[r.decision])

    # ──────────────────────────────────────────────────────────
    # أدوات مساعدة خاصة
    # ──────────────────────────────────────────────────────────

    def _decide_by_her(
        self,
        vaccine: EquipmentVaccine,
        her_ratio: float,
        ccm_index: str,
    ) -> VaccineAssessmentResult:
        """تطبيق عتبات HER لتحديد القرار."""
        ccm_note = f" | CCM={ccm_index}" if ccm_index != "0" else ""

        if her_ratio > HER_PARTIAL_MAX:
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.DISCARD,
                reason=DecisionReason.HEAT_EXCESS,
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                detail=(
                    f"HER={her_ratio:.4f} تجاوز الحد الأقصى "
                    f"{HER_PARTIAL_MAX}{ccm_note}"
                ),
            )

        if her_ratio > HER_SAFE_MAX:
            return self._result(
                vaccine=vaccine,
                decision=VaccineDecision.PARTIAL,
                reason=DecisionReason.PARTIAL_EXPOSURE,
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                detail=(
                    f"HER={her_ratio:.4f} في النطاق الجزئي "
                    f"({HER_SAFE_MAX}–{HER_PARTIAL_MAX}){ccm_note}"
                ),
            )

        return self._result(
            vaccine=vaccine,
            decision=VaccineDecision.SAFE,
            reason=DecisionReason.WITHIN_LIMITS,
            her_ratio=her_ratio,
            ccm_index=ccm_index,
            detail=f"HER={her_ratio:.4f} ضمن الحدود المقبولة{ccm_note}",
        )

    @staticmethod
    def _result(
        vaccine: EquipmentVaccine,
        decision: VaccineDecision,
        reason: DecisionReason,
        her_ratio: float,
        ccm_index: str,
        detail: str,
    ) -> VaccineAssessmentResult:
        """بناء نتيجة موحدة."""
        logger.info(
            "تقييم %s/%s → %s (%s)",
            vaccine.vaccine_type,
            vaccine.batch_number,
            decision.value.upper(),
            reason.value,
        )
        return VaccineAssessmentResult(
            equipment_id=vaccine.equipment_id,
            entry_id=vaccine.entry_id,
            vaccine_type=vaccine.vaccine_type,
            batch_number=vaccine.batch_number,
            expiry_date=vaccine.expiry_date,  # ✅ إضافة expiry_date
            decision=decision,
            reason=reason,
            her_ratio=her_ratio,
            ccm_index=ccm_index,
            decision_detail=detail,
        )
