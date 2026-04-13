# src/domain/calculators/q10_thermal_calculator.py
from __future__ import annotations

from typing import List, Union

from src.domain.ports.thermal_calculator_port import ThermalCalculatorPort
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class Q10ThermalCalculator(ThermalCalculatorPort):
    DEFAULT_Q10 = 2.0
    DEFAULT_MIN_TEMP = 2.0
    DEFAULT_MAX_TEMP = 8.0
    DEFAULT_EXCURSION_LIMIT_HOURS = 8.0

    def __init__(self, q10_value: float = DEFAULT_Q10):
        self.q10 = q10_value

    @staticmethod
    def _extract_spec_fields(spec) -> dict:
        return {
            "min_temp": float(getattr(spec, "min_temp", 2.0) or 2.0),
            "max_temp": float(getattr(spec, "max_temp", 8.0) or 8.0),
            "freeze_sensitive": bool(getattr(spec, "freeze_sensitive", False)),
            "excursion_time_limit": float(getattr(spec, "excursion_time_limit", 8.0) or 8.0),
        }

    @staticmethod
    def _resolve_reference_temp(reference_temp) -> float:
        if isinstance(reference_temp, (int, float)):
            return float(reference_temp)
        for attr in ("reference_temperature", "min_temp", "optimal_temp"):
            val = getattr(reference_temp, attr, None)
            if isinstance(val, (int, float)):
                return float(val)
        return 2.0

    def evaluate(self, temperature: float, duration_minutes: float, reference_temp) -> str:
        if duration_minutes < 0:
            raise ValueError("duration_minutes must be non-negative")

        # VaccineSpecification → business rules
        if not isinstance(reference_temp, (int, float)):
            return self._evaluate_with_spec(temperature, duration_minutes, reference_temp)

        # float → Q10 formula
        ref = float(reference_temp)
        factor = self.q10 ** ((temperature - ref) / 10.0)
        if factor >= 1.5:
            return "DISCARD"
        if factor >= 1.2:
            return "PARTIAL"
        return "SAFE"

    def _evaluate_with_spec(self, temperature: float, duration_minutes: float, spec) -> str:
        f = self._extract_spec_fields(spec)

        # 1. freeze-sensitive + below zero
        if f["freeze_sensitive"] and temperature <= 0.0:
            return "DISCARD"

        # 2. within safe range
        if f["min_temp"] <= temperature <= f["max_temp"]:
            return "SAFE"

        # 3. out of range — time-based judgment
        duration_hours = duration_minutes / 60.0
        limit = f["excursion_time_limit"]
        if duration_hours > limit:
            return "DISCARD"
        if duration_hours > limit / 2.0:
            return "PARTIAL"
        return "SAFE"

    def calculate_q10_impact(self, entries: List[TemperatureEntry], reference_temp) -> float:
        if not entries:
            return 1.0
        ref = self._resolve_reference_temp(reference_temp)
        total = sum(e.duration_minutes for e in entries)
        if total <= 0:
            return 1.0
        weighted = sum(
            (self.q10 ** ((e.temperature - ref) / 10.0)) * e.duration_minutes
            for e in entries
        )
        return weighted / total