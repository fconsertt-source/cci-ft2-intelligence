# src/infrastructure/mappers/temperature_mapper.py
from __future__ import annotations

from typing import List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.temperature_entry import TemperatureEntry


class TemperatureMapper:
    """
    يحوّل TemperatureEntry → TemperatureReading.

    DomainCenterContext يعمل على TemperatureEntry (domain pure).
    Calculators (ExposureAnalysisService) يعملون على TemperatureReading.
    هذا الـ Mapper هو نقطة العبور الوحيدة بينهما.

    التغيير في A4:
      يمرر duration_hours = duration_minutes / 60.0
      حتى يتمكن ExposureAnalysisService من الحساب الصحيح.
    """

    @staticmethod
    def entries_to_readings(
        entries: List[TemperatureEntry],
    ) -> List[TemperatureReading]:
        """
        تحويل قائمة TemperatureEntry إلى TemperatureReading.

        Args:
            entries: قائمة مدخلات درجة الحرارة من DomainCenterContext

        Returns:
            قائمة TemperatureReading جاهزة للـ ExposureAnalysisService
        """
        return [
            TemperatureReading(
                vaccine_id=entry.device_id,
                value=entry.temperature,
                recorded_at=entry.timestamp,
                duration_hours=entry.duration_minutes / 60.0,  # ← A4
                device_id=entry.device_id,
            )
            for entry in entries
        ]
