# src/domain/calculators/q10_her_calculator.py
from __future__ import annotations

import math
from typing import Dict, List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.her_result import HERResult

# ============================================================================
# SCIENTIFIC CONSTANTS — WHO/IVB/06.10
# Q10 = 2.0  للمنتجات البيولوجية العامة (Box 1)
# Tref = 5.0°C  درجة مرجعية اصطلاحية (VVM baseline)
# SHELF_LIFE_HOURS = 48h  حد افتراضي محافظ (قابل للتخصيص لكل لقاح)
# max_gap = 2.0h  حد فجوة القياس — ما فوقه يُقيَّد
# ============================================================================
DEFAULT_Q10 = 2.0
DEFAULT_REFERENCE_TEMP = 5.0
DEFAULT_SHELF_LIFE_HOURS = 48.0  # ✅ اسم موحد مع الاختبار
DEFAULT_MAX_GAP_HOURS = 2.0

# للتوافق الخلفي مع الكود القديم
DEFAULT_shelf_life_hours = DEFAULT_SHELF_LIFE_HOURS


class Q10HerCalculator:
    """
    حساب Heat Exposure Ratio باستخدام نموذج Q10 العلمي.

    المعادلة:
        HER = Σ [ Q10^((T_avg - T_ref)/10) × Δt ]

    حيث T_avg = متوسط درجتي الحرارة للفترة (midpoint — أدق من T_current).

    مقاوم لفجوات القياس (sampling gaps):
        أي Δt > max_gap_hours يُقيَّد إلى max_gap_hours
        ويُسجَّل في data_quality_flags["sampling_gap"].

    المرجع: WHO/IVB/06.10 — Box 1 (Accelerated Degradation Test)
    """

    def __init__(
        self,
        q10_value: float = DEFAULT_Q10,
        reference_temp: float = DEFAULT_REFERENCE_TEMP,
        shelf_life_hours: float = DEFAULT_SHELF_LIFE_HOURS,  # ✅ اسم موحد
        max_gap_hours: float = DEFAULT_MAX_GAP_HOURS,
    ) -> None:
        if q10_value <= 0:
            raise ValueError(f"Q10 يجب أن يكون موجباً: {q10_value}")
        if shelf_life_hours <= 0:
            raise ValueError(f"shelf_life_hours يجب أن يكون موجباً: {shelf_life_hours}")
        if max_gap_hours <= 0:
            raise ValueError(f"max_gap_hours يجب أن يكون موجباً: {max_gap_hours}")

        self._q10 = q10_value
        self._t_ref = reference_temp
        self._shelf_life = shelf_life_hours  # ✅ اسم الخاصية الجديد
        self._max_gap = max_gap_hours


    def calculate_her(self, readings: List[TemperatureReading]) -> HERResult:
        """
        حساب HER من قائمة قراءات درجة الحرارة.
        هذه هي الدالة الأساسية.
        """
        data_quality_flags: Dict[str, bool] = {"sampling_gap": False}

        if len(readings) < 2:
            return HERResult(
                cumulative_degradation_hours=0.0,
                her_ratio=0.0,
                readings_count=len(readings),
                q10_value_used=self._q10,
                reference_temp_used=self._t_ref,
                data_quality_flags=data_quality_flags,
            )

        sorted_readings = sorted(readings, key=lambda r: r.recorded_at)
        her_hours = 0.0

        for i in range(len(sorted_readings) - 1):
            prev = sorted_readings[i]
            curr = sorted_readings[i + 1]

            # المدة الحقيقية بالساعات
            raw_delta_hours = (
                curr.recorded_at - prev.recorded_at
            ).total_seconds() / 3600.0

            if raw_delta_hours <= 0:
                continue

            # تقييد فجوات القياس الكبيرة
            if raw_delta_hours > self._max_gap:
                data_quality_flags["sampling_gap"] = True
                delta_hours = self._max_gap
            else:
                delta_hours = raw_delta_hours

            # متوسط درجة الحرارة للفترة
            avg_temp = (prev.value + curr.value) / 2.0

            # عامل التسريع Q10
            exponent = (avg_temp - self._t_ref) / 10.0
            try:
                factor = math.pow(self._q10, exponent)
            except (ValueError, OverflowError):
                factor = float("inf")

            if math.isinf(factor) or math.isnan(factor):
                her_hours = float("inf")
                break

            her_hours += factor * delta_hours

        # حساب النسبة
        if math.isinf(her_hours):
            her_ratio = float("inf")
        else:
            her_ratio = her_hours / self._shelf_life

        return HERResult(
            cumulative_degradation_hours=her_hours,
            her_ratio=her_ratio,
            readings_count=len(readings),
            q10_value_used=self._q10,
            reference_temp_used=self._t_ref,
            data_quality_flags=data_quality_flags,
        )

    def calculate(self, readings: List[TemperatureReading]) -> HERResult:
        """
        واجهة متوافقة مع الاختبارات - تستدعي calculate_her
        """
        return self.calculate_her(readings)