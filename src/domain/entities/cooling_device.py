# src/domain/entities/cooling_device.py
"""
A4 — إصلاح CoolingDevice.evaluate_safety()

المشكلة القديمة:
  her = avg_temp * len(readings) / 1440.0  ← خاطئة علمياً كلياً
  عتبات her < 10 / her < 20              ← أرقام عشوائية بلا أساس

الإصلاح:
  استخدام ExposureAnalysisService (Q10 + CCM + Circuit Breakers)
  عتبات HER_SAFE_MAX=1.0 و HER_PARTIAL_MAX=1.5 من WHO/IVB/06.10
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.domain.enums.vvm_stage import VVMStage
from src.domain.services.exposure_analysis_service import ExposureAnalysisService
from src.domain.value_objects.vaccine_specification import (
    VaccineSpecification,
    get_vaccine_spec,
    HER_SAFE_MAX,
    HER_PARTIAL_MAX,
)

# ──────────────────────────────────────────────────────────────
# عتبات القرار — WHO/IVB/06.10
# ──────────────────────────────────────────────────────────────
_HER_SAFE: float = HER_SAFE_MAX      # ≤ 1.0  → SAFE
_HER_PARTIAL: float = HER_PARTIAL_MAX  # ≤ 1.5  → PARTIAL
# > 1.5 → DISCARD


@dataclass(frozen=True)
class DeviceSafetyResult:
    """نتيجة تقييم سلامة جهاز واحد."""

    device_id: str
    status: str        # SAFE | PARTIAL | DISCARD | NO_DATA
    her: float         # HER ratio (0.0 → ∞)
    ccm: str           # CCM index (0 | A | AB | ABC | D)
    vvm_stage: VVMStage
    circuit_breaker: Optional[str] = None  # سبب الوقف الفوري إن وجد
    max_temp: float = 0.0
    min_temp: float = 0.0
    decision_reason: str = ""


@dataclass(frozen=True)
class CoolingDevice:
    """
    معدة التبريد الفيزيائية — Berlinger Fridge-tag® 2 E.

    الحقول الوصفية (location, capacity_liters) لا تدخل في الحسابات.
    التقييم يعتمد حصراً على القراءات الحرارية + مواصفات اللقاح.
    """

    device_id: str
    location: str           # وصفي فقط
    vaccine_type: str
    capacity_liters: float  # وصفي فقط

    def evaluate_safety(
        self,
        readings: List,
        spec: Optional[VaccineSpecification] = None,
    ) -> DeviceSafetyResult:
        """
        تقييم سلامة هذا الجهاز فقط — لا تجميع.

        التدفق:
          1. بيانات فارغة → NO_DATA
          2. جلب مواصفات اللقاح (من spec أو من vaccine_type)
          3. تشغيل ExposureAnalysisService (Q10 + CCM + Circuit Breakers)
          4. تطبيق منطق القرار وفق HER ratio و circuit_breaker

        Args:
            readings: قائمة القراءات الحرارية (تحتوي .value و .duration_minutes)
            spec:     مواصفات اللقاح (اختيارية — يُستنبط من vaccine_type عند غيابها)

        Returns:
            DeviceSafetyResult يحتوي على HER و CCM والقرار النهائي
        """
        # ── 1. بيانات فارغة ──────────────────────────────────
        if not readings:
            return DeviceSafetyResult(
                device_id=self.device_id,
                status="NO_DATA",
                her=0.0,
                ccm="0",
                vvm_stage=VVMStage.NONE,
                decision_reason="لا توجد بيانات حرارية",
            )

        # ── 2. مواصفات اللقاح ────────────────────────────────
        if spec is None:
            spec = get_vaccine_spec(self.vaccine_type)

        # ── 3. تحليل التعرض الحراري (Q10 + CCM) ─────────────
        analysis = ExposureAnalysisService().analyze(
            readings=readings,
            spec=spec,
        )

        her_ratio = analysis["her_ratio"]
        ccm_index = analysis["ccm_index"]
        circuit_breaker = analysis["circuit_breaker"]
        max_temp = analysis["max_temp"]
        min_temp = analysis["min_temp"]

        # ── 4. منطق القرار ───────────────────────────────────
        status, vvm_stage, reason = self._decide(
            her_ratio=her_ratio,
            ccm_index=ccm_index,
            circuit_breaker=circuit_breaker,
            spec=spec,
        )

        return DeviceSafetyResult(
            device_id=self.device_id,
            status=status,
            her=her_ratio,
            ccm=ccm_index,
            vvm_stage=vvm_stage,
            circuit_breaker=circuit_breaker,
            max_temp=max_temp,
            min_temp=min_temp,
            decision_reason=reason,
        )

    @staticmethod
    def _decide(
        her_ratio: float,
        ccm_index: str,
        circuit_breaker: Optional[str],
        spec: VaccineSpecification,
    ) -> tuple[str, VVMStage, str]:
        """
        منطق القرار الهرمي (Waterfall):

          المستوى 1 — Circuit Breaker (أولوية مطلقة)
            FREEZE_EXCURSION  → DISCARD فوري
            CRITICAL_HEAT_34C → DISCARD فوري

          المستوى 2 — CCM Index D
            → DISCARD

          المستوى 3 — HER ratio
            > 1.5  → DISCARD
            > 1.0  → PARTIAL
            ≤ 1.0  → SAFE

        Returns:
            (status, vvm_stage, reason)
        """
        # ── المستوى 1: Circuit Breaker ────────────────────────
        if circuit_breaker == "FREEZE_EXCURSION":
            return (
                "DISCARD",
                VVMStage.D,
                f"تجمد مكتشف — لقاح {spec.vaccine_type} حساس للتجمد",
            )

        if circuit_breaker == "CRITICAL_HEAT_34C":
            return (
                "DISCARD",
                VVMStage.D,
                f"حرارة حرجة فوق 34°C لأكثر من {spec.critical_hours:.0f} ساعات",
            )

        # ── المستوى 2: CCM Index D ────────────────────────────
        if ccm_index == "D":
            return (
                "DISCARD",
                VVMStage.D,
                "مؤشر CCM وصل للنافذة D (فوق 34°C)",
            )

        # ── المستوى 3: HER ratio ──────────────────────────────
        if her_ratio > _HER_PARTIAL:
            return (
                "DISCARD",
                VVMStage.C,
                f"HER ratio={her_ratio:.3f} تجاوز الحد الأقصى {_HER_PARTIAL}",
            )

        if her_ratio > _HER_SAFE:
            return (
                "PARTIAL",
                VVMStage.B,
                f"HER ratio={her_ratio:.3f} في النطاق الجزئي ({_HER_SAFE}–{_HER_PARTIAL})",
            )

        # ── آمن ──────────────────────────────────────────────
        ccm_note = f" — CCM={ccm_index}" if ccm_index != "0" else ""
        return (
            "SAFE",
            VVMStage.A,
            f"HER ratio={her_ratio:.3f} ضمن الحدود المقبولة{ccm_note}",
        )