# ============================================================================
# DECISION LOCK: TIME UNIT SOURCE OF TRUTH
# 🔒 DO NOT CHANGE without updating contracts and all tests
# ============================================================================
from typing import Any, Dict, List


from src.domain.entities.temperature_reading import TemperatureReading

TIME_UNIT = "minutes"

def calculate_delta_minutes(record: Dict[str, Any]) -> float:
    """
    Helper used by CCM routines.

    IMPORTANT:
    delta_minutes is intentionally in minutes (not seconds)
    to match CCM domain expectations.  The previous incarnation of this
    helper mistakenly returned seconds which caused subtle off-by-60 bugs
    in early CCM reports; the tests now exercise this directly.
    """
    delta = record["timestamp"] - record["previous_timestamp"]
    return delta.total_seconds() / 60


# ccm_calculator.py (مُحسّن)
class CCMCalculator:
    """يحسب التراكم الحراري بطرق متعددة"""

    def __init__(self, threshold: float = 1.0, method: str = "delta"):
        self.threshold = threshold
        self.method = method  # "delta", "auc", "both"

    def calculate_delta(self, readings: List[TemperatureReading]) -> float:
        """الطريقة الأصلية (الفروقات المطلقة)"""
        if len(readings) < 2:
            return 0.0

        readings = sorted(readings, key=lambda r: r.recorded_at)
        ccm = 0.0
        prev_temp = readings[0].value

        for r in readings[1:]:
            delta = abs(r.value - prev_temp)
            if delta >= self.threshold:
                ccm += delta
            prev_temp = r.value

        return ccm

    def calculate_auc(
        self, readings: List[TemperatureReading], base_temp: float = 8.0
    ) -> float:
        """حساب المساحة تحت المنحنى فوق درجة حرارة أساسية"""
        if len(readings) < 2:
            return 0.0

        readings = sorted(readings, key=lambda r: r.recorded_at)
        total_auc = 0.0

        for i in range(len(readings) - 1):
            t1, temp1 = readings[i].recorded_at, readings[i].value
            t2, temp2 = readings[i + 1].recorded_at, readings[i + 1].value

            # calculate the time difference in minutes (see TIME_UNIT)
            delta_minutes = calculate_delta_minutes(
                {
                    "timestamp": t2,
                    "previous_timestamp": t1,
                }
            )

            # defensive: ignore non-positive gaps (duplicates, clock skew, etc.)
            if delta_minutes <= 0:
                continue

            # حساب المساحة شبه المنحرفة فوق درجة الأساس
            if temp1 > base_temp or temp2 > base_temp:
                # متوسط الحرارة فوق الأساس
                avg_excess = (max(0, temp1 - base_temp) + max(0, temp2 - base_temp)) / 2

                # المساحة = المتوسط × الزمن
                total_auc += avg_excess * delta_minutes

        return total_auc

    def calculate(self, readings: List[TemperatureReading]) -> Dict[str, float]:
        """إرجاع جميع المقاييس"""
        return {
            "ccm_delta": self.calculate_delta(readings),
            "ccm_auc": self.calculate_auc(readings),
            "method_used": self.method,
        }
