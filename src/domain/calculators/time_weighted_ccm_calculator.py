# src/domain/calculators/time_weighted_ccm_calculator.py
from __future__ import annotations

from typing import List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.ccm_result import CCMResult


# ============================================================================
# DECISION LOCK: TIME UNIT SOURCE OF TRUTH
# 🔒 متوافق مع ccm_calculator.py — الوحدة: دقائق
# ============================================================================
DEFAULT_BASE_TEMP = 8.0   # °C — نهاية نطاق التخزين الموصى به (WHO: 2–8°C)
DEFAULT_THRESHOLD = 1.0   # °C — حد التغيير المعتبر في طريقة Delta


class TimeWeightedCcmCalculator:
    """
    حساب Cold Chain Monitor الموزون زمنياً.

    يُحسن على CCMCalculator الأساسي بإضافة:
    - الوزن الزمني للفترات (فترة أطول = تأثير أكبر)
    - حساب AUC الحراري الدقيق بالتكامل الشبه منحرف
    - حفظ المدة الكلية لتمكين مقارنات مطبّعة

    مستقل تماماً عن HER — لا يشارك حالة، لا يؤثر على نتائجه.

    المرجع: CCM domain model — time-weighted cold chain cumulation
    """

    def __init__(
        self,
        base_temp: float = DEFAULT_BASE_TEMP,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        """
        Args:
            base_temp: درجة الحرارة الأساسية لحساب AUC (افتراضي 8.0°C)
            threshold: حد الفرق الأدنى لاعتبار التغيير في طريقة Delta (افتراضي 1.0°C)
        """
        self._base_temp = base_temp
        self._threshold = threshold

    def calculate(self, readings: List[TemperatureReading]) -> CCMResult:
        """
        حساب CCM من قائمة قراءات درجة الحرارة.

        الخوارزمية:
        طريقة Delta (كلاسيكية):
            - مجموع الفروقات المطلقة ≥ threshold بين القراءات المتتالية
            - مستقلة عن الزمن: تقيس التقلب الحراري

        طريقة AUC (موزونة زمنياً):
            - تكامل شبه منحرف لدرجة الحرارة فوق base_temp
            - الوحدة: degree-minutes
            - تعكس التحميل الحراري الفعلي بدقة أعلى

        Args:
            readings: قائمة قراءات درجة الحرارة (غير مرتبة مقبولة)

        Returns:
            CCMResult: نتيجة الحساب — قيمة نقية بدون حكم
        """
        if len(readings) < 2:
            return CCMResult(
                ccm_delta=0.0,
                ccm_auc=0.0,
                base_temp_used=self._base_temp,
                readings_count=len(readings),
                total_duration_minutes=0.0,
            )

        sorted_readings = sorted(readings, key=lambda r: r.recorded_at)

        ccm_delta = 0.0
        ccm_auc = 0.0
        total_duration_minutes = 0.0
        prev_temp = sorted_readings[0].value

        for i in range(len(sorted_readings) - 1):
            r1 = sorted_readings[i]
            r2 = sorted_readings[i + 1]

            # المدة بالدقائق (TIME_UNIT = minutes — متوافق مع ccm_calculator.py)
            delta_seconds = (r2.recorded_at - r1.recorded_at).total_seconds()
            if delta_seconds <= 0:
                prev_temp = r2.value
                continue

            delta_minutes = delta_seconds / 60.0
            total_duration_minutes += delta_minutes

            # --- طريقة Delta ---
            temp_diff = abs(r2.value - prev_temp)
            if temp_diff >= self._threshold:
                ccm_delta += temp_diff
            prev_temp = r2.value

            # --- طريقة AUC (تكامل شبه منحرف) ---
            temp1 = r1.value
            temp2 = r2.value

            if temp1 > self._base_temp or temp2 > self._base_temp:
                excess1 = max(0.0, temp1 - self._base_temp)
                excess2 = max(0.0, temp2 - self._base_temp)
                avg_excess = (excess1 + excess2) / 2.0
                ccm_auc += avg_excess * delta_minutes

        return CCMResult(
            ccm_delta=ccm_delta,
            ccm_auc=ccm_auc,
            base_temp_used=self._base_temp,
            readings_count=len(readings),
            total_duration_minutes=total_duration_minutes,
        )