# src/domain/services/exposure_analysis_service.py
"""
ExposureAnalysisService — محرك التحليل الحراري التراكمي
المصدر العلمي: WHO/IVB/06.10 + WHO/PQS/E06/IN02.1

مسؤوليات هذه الخدمة:
  1. تطبيق Circuit Breakers (تجمد / حرارة حرجة) — قرار فوري
  2. حساب HER ratio عبر نموذج Q10 (Arrhenius)
  3. تحديد CCM index (A/B/C/D) وفق WHO/PQS/E06/IN02.1
  4. إرجاع تحليل موحد يُغذّي RulesEngine

لا تتخذ هذه الخدمة قرارات نهائية — تُنتج إحصاءات فقط.
القرار النهائي يبقى في RulesEngine.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.temperature_reading import TemperatureReading
    from src.domain.value_objects.vaccine_specification import VaccineSpecification

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# عتبات CCM الرسمية — WHO/PQS/E06/IN02.1 § 4.2.3
# ──────────────────────────────────────────────────────────────
_CCM_UPPER_THRESHOLD: float = 10.0   # نافذة +10°C
_CCM_CRITICAL_THRESHOLD: float = 34.0  # نافذة +34°C (D)
_CCM_CRITICAL_HOURS: float = 2.0     # ساعتان فوق 34°C = DISCARD

# عتبات HER
_HER_SAFE_MAX: float = 1.0
_HER_PARTIAL_MAX: float = 1.5

# عتبة التجمد
_FREEZE_THRESHOLD: float = -0.5


class ExposureAnalysisService:
    """
    محرك التحليل الحراري التراكمي.

    يعمل على قائمة TemperatureReading ويُنتج dict موحداً
    يحتوي على جميع المؤشرات المطلوبة لـ RulesEngine.
    """

    def analyze(
        self,
        readings: List["TemperatureReading"],
        spec: Optional["VaccineSpecification"] = None,
    ) -> Dict:
        """
        تحليل السجل الحراري الكامل.

        Args:
            readings: قائمة القراءات الحرارية مرتبة زمنياً
            spec:     مواصفات اللقاح (اختيارية — يستخدم الافتراضي عند غيابها)

        Returns:
            dict يحتوي على:
              - her_ratio:          نسبة استهلاك العمر الافتراضي (0.0 → ∞)
              - ccm_index:          مؤشر CCM (0/A/B/C/D)
              - has_freeze:         هل حدث تجمد؟
              - has_critical_heat:  هل تجاوز 34°C لأكثر من ساعتين؟
              - max_temp:           أعلى درجة مسجلة
              - min_temp:           أدنى درجة مسجلة
              - total_hours_above_10: إجمالي ساعات فوق 10°C
              - total_hours_above_34: إجمالي ساعات فوق 34°C
              - circuit_breaker:    سبب الوقف الفوري (None إن لم يوجد)
        """
        if not readings:
            return self._empty_analysis()

        # جلب المواصفة الافتراضية عند الغياب
        if spec is None:
            from src.domain.value_objects.vaccine_specification import (
                VACCINE_CATALOGUE,
            )
            spec = VACCINE_CATALOGUE["GENERAL"]

        # ── 1. Circuit Breakers (أولوية مطلقة) ──────────────────
        circuit_breaker = self._check_circuit_breakers(readings, spec)

        # ── 2. إحصاءات أساسية ───────────────────────────────────
        temps = [r.value for r in readings]
        max_temp = max(temps)
        min_temp = min(temps)

        # ── 3. ساعات التعرض فوق العتبات ─────────────────────────
        hours_above_10 = self._cumulative_hours_above(readings, _CCM_UPPER_THRESHOLD)
        hours_above_34 = self._cumulative_hours_above(readings, _CCM_CRITICAL_THRESHOLD)

        # ── 4. CCM Index ─────────────────────────────────────────
        ccm_index = self._calculate_ccm_index(hours_above_10, hours_above_34)

        # ── 5. Q10 HER ratio ─────────────────────────────────────
        her_ratio = self._calculate_her_ratio(readings, spec)

        logger.debug(
            "ExposureAnalysis: max=%.1f°C min=%.1f°C "
            "HER=%.3f CCM=%s freeze=%s critical=%s",
            max_temp, min_temp, her_ratio, ccm_index,
            min_temp < _FREEZE_THRESHOLD,
            hours_above_34 >= _CCM_CRITICAL_HOURS,
        )

        return {
            "her_ratio": her_ratio,
            "ccm_index": ccm_index,
            "has_freeze": min_temp < _FREEZE_THRESHOLD,
            "has_critical_heat": hours_above_34 >= _CCM_CRITICAL_HOURS,
            "max_temp": max_temp,
            "min_temp": min_temp,
            "total_hours_above_10": round(hours_above_10, 2),
            "total_hours_above_34": round(hours_above_34, 4),
            "circuit_breaker": circuit_breaker,
        }

    # ──────────────────────────────────────────────────────────
    # Circuit Breakers
    # ──────────────────────────────────────────────────────────

    def _check_circuit_breakers(
        self,
        readings: List["TemperatureReading"],
        spec: "VaccineSpecification",
    ) -> Optional[str]:
        """
        تحقق من الخروق الحرجة الفورية.

        الأولوية:
          1. تجمد (للقاحات الحساسة فقط)
          2. حرارة فوق 34°C لأكثر من ساعتين
        """
        # تجمد — فقط للقاحات الحساسة (ألومنيوم)
        if spec.freeze_sensitive:
            min_temp = min(r.value for r in readings)
            if min_temp < _FREEZE_THRESHOLD:
                logger.warning(
                    "CIRCUIT_BREAKER: FREEZE detected (min=%.2f°C) "
                    "for freeze-sensitive vaccine %s",
                    min_temp, spec.vaccine_type,
                )
                return "FREEZE_EXCURSION"

        # حرارة حرجة فوق 34°C لأكثر من ساعتين
        hours_critical = self._cumulative_hours_above(readings, _CCM_CRITICAL_THRESHOLD)
        if hours_critical >= spec.critical_hours:
            logger.warning(
                "CIRCUIT_BREAKER: CRITICAL_HEAT (%.2f hrs above %.0f°C)",
                hours_critical, _CCM_CRITICAL_THRESHOLD,
            )
            return "CRITICAL_HEAT_34C"

        return None

    # ──────────────────────────────────────────────────────────
    # Q10 HER Calculation — Arrhenius Model
    # ──────────────────────────────────────────────────────────

    def _calculate_her_ratio(
        self,
        readings: List["TemperatureReading"],
        spec: "VaccineSpecification",
    ) -> float:
        """
        حساب HER ratio وفق نموذج Q10 (Arrhenius).

        يدعم كلا الحقلين:
          - duration_minutes (TemperatureEntry / FT2Reading)
          - duration_hours   (TemperatureReading domain entity)
        """
        if not readings or spec.shelf_life_hours <= 0:
            return 0.0

        cumulative_degradation_hours: float = 0.0

        for reading in readings:
            # دعم duration_minutes و duration_hours معاً
            duration_hours = self._get_duration_hours(reading)

            # عامل التسريع Q10
            exponent = (reading.value - spec.reference_temp_c) / 10.0
            factor = spec.q10_factor ** exponent

            cumulative_degradation_hours += duration_hours * factor

        her_ratio = cumulative_degradation_hours / spec.shelf_life_hours

        logger.debug(
            "Q10 HER: cumulative_deg=%.4f hrs / shelf=%.1f hrs = ratio=%.4f",
            cumulative_degradation_hours,
            spec.shelf_life_hours,
            her_ratio,
        )

        return round(her_ratio, 6)

    # ──────────────────────────────────────────────────────────
    # CCM Index — WHO/PQS/E06/IN02.1 § 4.2.3
    # ──────────────────────────────────────────────────────────

    def _calculate_ccm_index(
        self,
        hours_above_10: float,
        hours_above_34: float,
    ) -> str:
        """
        تحديد CCM index وفق عتبات WHO الرسمية.

        الجدول (من § 4.2.6):
          - فوق 34°C لأكثر من ساعتين       → D
          - فوق 10°C لأكثر من 336 ساعة     → ABC (14 يوم)
          - فوق 10°C بين 192-336 ساعة      → AB  (8-14 يوم)
          - فوق 10°C بين 72-192 ساعة       → A   (3-8 يوم)
          - فوق 10°C أقل من 72 ساعة        → 0   (آمن)
        """
        # النافذة D — الأحرج
        if hours_above_34 >= _CCM_CRITICAL_HOURS:
            return "D"

        # النوافذ A/B/C — تراكمي
        if hours_above_10 >= 336.0:   # 14 يوم × 24
            return "ABC"
        elif hours_above_10 >= 192.0:  # 8 يوم × 24
            return "AB"
        elif hours_above_10 >= 72.0:   # 3 يوم × 24
            return "A"
        else:
            return "0"

    # ──────────────────────────────────────────────────────────
    # أدوات مساعدة
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _get_duration_hours(reading) -> float:
        """
        استخراج مدة القراءة بالساعات من أي نوع قراءة.

        يدعم:
          - duration_minutes (TemperatureEntry / FT2Reading / MagicMock في الاختبارات)
          - duration_hours   (TemperatureReading domain entity)
          - افتراضي 24 ساعة عند غياب كليهما (قراءة يومية)
        """
        # أولاً: duration_minutes (الأكثر شيوعاً)
        minutes = getattr(reading, "duration_minutes", None)
        if minutes is not None:
            return float(minutes) / 60.0

        # ثانياً: duration_hours (TemperatureReading)
        hours = getattr(reading, "duration_hours", None)
        if hours is not None:
            return float(hours)

        # افتراضي: قراءة يومية
        return 24.0

    @staticmethod
    def _cumulative_hours_above(
        readings: List["TemperatureReading"],
        threshold: float,
    ) -> float:
        """
        حساب إجمالي ساعات التعرض فوق عتبة معينة.

        يدعم duration_minutes و duration_hours معاً.
        """
        total_hours: float = 0.0
        for reading in readings:
            if reading.value > threshold:
                # استخدام نفس منطق _get_duration_hours
                minutes = getattr(reading, "duration_minutes", None)
                if minutes is not None:
                    total_hours += float(minutes) / 60.0
                else:
                    hours = getattr(reading, "duration_hours", None)
                    total_hours += float(hours) if hours is not None else 24.0
        return total_hours

    @staticmethod
    def _empty_analysis() -> Dict:
        """نتيجة فارغة عند غياب البيانات."""
        return {
            "her_ratio": 0.0,
            "ccm_index": "0",
            "has_freeze": False,
            "has_critical_heat": False,
            "max_temp": 0.0,
            "min_temp": 0.0,
            "total_hours_above_10": 0.0,
            "total_hours_above_34": 0.0,
            "circuit_breaker": None,
        }