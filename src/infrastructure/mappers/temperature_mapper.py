# src/infrastructure/mappers/temperature_mapper.py
from __future__ import annotations

from typing import List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.temperature_entry import TemperatureEntry


class TemperatureMapper:
    """
    يحوّل TemperatureEntry → TemperatureReading.

    DomainCenterContext يعمل على TemperatureEntry (domain pure).
    Calculators (Q10HerCalculator) يعملون على TemperatureReading.
    هذا الـ Mapper هو نقطة العبور الوحيدة بينهما.

    موضوع في infrastructure لأنه تحويل بنية بيانات،
    وليس منطق domain.
    """

    @staticmethod
    def entries_to_readings(entries: List[TemperatureEntry]) -> List[TemperatureReading]:
        """
        تحويل قائمة TemperatureEntry إلى TemperatureReading.

        TemperatureEntry يحتوي على duration_minutes (مُحسوبة من pairwise).
        TemperatureReading يحتوي على recorded_at (timestamp).
        كلاهما يشيران لنفس القراءة — الفرق في الاستخدام فقط.

        Args:
            entries: قائمة مدخلات درجة الحرارة من DomainCenterContext

        Returns:
            قائمة TemperatureReading جاهزة للـ Q10HerCalculator
        """
        return [
            TemperatureReading(
                vaccine_id=entry.device_id,
                value=entry.temperature,
                recorded_at=entry.timestamp,
            )
            for entry in entries
        ]