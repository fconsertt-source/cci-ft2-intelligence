from __future__ import annotations

import math
from typing import Iterable

from src.domain.value_objects.her_result import HERResult
from src.domain.value_objects.temperature_entry import TemperatureEntry

# Constants for Arrhenius-based thermal exposure modeling
DEFAULT_EA_KJ_MOL = 83.144
DEFAULT_REFERENCE_TEMP_C = 5.0
R_J_MOL_K = 8.314


class ArrheniusHERCalculator:
    """
    Scientific reference calculator for Heat Exposure Ratio using Arrhenius.

    This implementation is intended for the parallel reference engine only.
    """

    def __init__(
        self,
        ea_kj_mol: float = DEFAULT_EA_KJ_MOL,
        reference_temp_c: float = DEFAULT_REFERENCE_TEMP_C,
    ) -> None:
        if ea_kj_mol <= 0:
            raise ValueError("Ea must be positive")

        self.ea_j_mol = ea_kj_mol * 1000.0
        self.reference_temp_c = reference_temp_c

    def calculate(self, entries: Iterable[TemperatureEntry], shelf_life_hours: float) -> HERResult:
        cumulative_degradation_hours = 0.0
        readings_count = 0
        data_quality_flags = {"sampling_gap": False}

        for entry in entries:
            duration_hours = float(entry.duration_minutes) / 60.0
            if duration_hours <= 0.0:
                continue

            temperature_c = float(entry.temperature)
            temp_k = temperature_c + 273.15
            ref_k = self.reference_temp_c + 273.15

            if temp_k <= 0.0:
                continue

            exponent = (1.0 / ref_k) - (1.0 / temp_k)
            try:
                factor = math.exp(self.ea_j_mol * exponent / R_J_MOL_K)
            except OverflowError:
                factor = float("inf")

            cumulative_degradation_hours += duration_hours * factor
            readings_count += 1

        her_ratio = 0.0
        if shelf_life_hours > 0:
            her_ratio = cumulative_degradation_hours / shelf_life_hours

        return HERResult(
            cumulative_degradation_hours=cumulative_degradation_hours,
            her_ratio=her_ratio,
            readings_count=readings_count,
            q10_value_used=0.0,
            reference_temp_used=self.reference_temp_c,
            data_quality_flags=data_quality_flags,
        )
