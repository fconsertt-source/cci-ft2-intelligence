"""
Test Time Factory — Self-documenting helpers لمنع خلط الوحدات الزمنية

Usage:
    from tests.helpers.time_factory import create_reading, minutes, hours

    # واضح ودلالي:
    create_reading(9.0, minutes(60), base)   # 60 دقيقة
    create_reading(10.0, hours(2), base)     # ساعتين
"""

from datetime import datetime, timedelta
from typing import Optional

from src.domain.entities.temperature_reading import TemperatureReading


def minutes(n: float) -> float:
    """
    Self-documenting helper: صرّح أن القيمة بالدقائق.
    """
    return float(n)


def hours(n: float) -> float:
    """تحويل الساعات إلى دقائق للاستخدام في create_reading"""
    return float(n * 60)


def create_reading(
    value: float,
    delta: float,  # ✅ استخدم minutes() أو hours() للوضوح
    base_time: Optional[datetime] = None,
    vaccine_id: str = "test_vaccine",
) -> TemperatureReading:
    """
    إنشاء قراءة حرارية لأغراض الاختبار.

    IMPORTANT:
    - delta MUST be in MINUTES (استخدم minutes() أو hours() للوضوح)
    - This matches CCMCalculator.TIME_UNIT = "minutes"

    Example:
        create_reading(9.0, minutes(60), base)  # قراءة بعد 60 دقيقة
        create_reading(10.0, hours(2), base)     # قراءة بعد ساعتين
    """
    if base_time is None:
        base_time = datetime(2025, 1, 1, 0, 0, 0)

    # ✅ التحويل الصريح: دقائق → ثواني لـ timedelta
    recorded_at = base_time + timedelta(minutes=delta)

    return TemperatureReading(
        vaccine_id=vaccine_id, value=value, recorded_at=recorded_at
    )
