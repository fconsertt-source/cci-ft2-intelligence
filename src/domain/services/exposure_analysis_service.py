# src/domain/services/exposure_analysis_service.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.domain.calculators.q10_her_calculator import Q10HerCalculator
from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.vaccine_specification import VaccineSpecification

# ============================================================================
# ANALYSIS RESULT SCHEMA
# يُمرَّر مباشرةً كـ extra_stats إلى apply_rules()
# ============================================================================
# her_ratio        : float  — نسبة HER (0.0–∞)
# data_quality_flags: dict  — {"sampling_gap": bool, ...}
# ============================================================================


class ExposureAnalysisService:
    """
    Domain Service يجمع كل حسابات التعرض الحراري في مكان واحد.

    Phase 6.1: HER فقط.
    Phase 6.2: يُضاف CCM بدون تعديل UseCase.

    لا يُصدر قرارات — مسؤوليته الحساب فقط.
    القرار يبقى في RulesEngine.
    """

    def __init__(
        self,
        q10_value: float = 2.0,
        reference_temp: float = 5.0,
        shelf_life_hours: float = 48.0,
        max_gap_hours: float = 0.5,
    ) -> None:
        self._her_calculator = Q10HerCalculator(
            q10_value=q10_value,
            reference_temp=reference_temp,
            shelf_life_hours=shelf_life_hours,
            max_gap_hours=max_gap_hours,
        )

    def analyze(
        self,
        readings: List[TemperatureReading],
        spec: Optional[VaccineSpecification] = None,
    ) -> Dict[str, Any]:
        """
        تحليل التعرض الحراري وإرجاع النتائج كـ dict جاهز لـ apply_rules.

        Args:
            readings: قراءات درجة الحرارة (TemperatureReading)
            spec: مواصفات اللقاح (اختياري — يُستخدم لاحقاً لتخصيص Q10)

        Returns:
            dict يُمرَّر مباشرةً كـ extra_stats إلى apply_rules():
            {
                "her_ratio": float,
                "data_quality_flags": {"sampling_gap": bool}
            }
        """
        # تخصيص Q10 من spec إذا أُضيف الحقل لاحقاً
        # حالياً يستخدم القيمة الافتراضية
        her_result = self._her_calculator.calculate(readings)

        return {
            "her_ratio": her_result.her_ratio,
            "data_quality_flags": her_result.data_quality_flags,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Phase 6.2 — CCM يُضاف هنا بدون تعديل UseCase
    # ──────────────────────────────────────────────────────────────────────
    # def analyze(self, readings, spec=None):
    #     her_result = self._her_calculator.calculate(readings)
    #     ccm_result = self._ccm_calculator.calculate(readings)
    #     return {
    #         "her_ratio": her_result.her_ratio,
    #         "ccm_auc": ccm_result.ccm_auc,
    #         "data_quality_flags": her_result.data_quality_flags,
    #     }