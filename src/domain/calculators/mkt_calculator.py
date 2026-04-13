from __future__ import annotations

import math
from typing import Iterable

from src.domain.value_objects.temperature_entry import TemperatureEntry

# Scientific constants
R_J_MOL_K = 8.314
DEFAULT_EA_KJ_MOL = 83.144
DEFAULT_REFERENCE_TEMP_C = 5.0


class MKTCalculator:
    """
    Mean Kinetic Temperature calculator supporting audit-only reference checks.
    """

    def __init__(
        self,
        ea_kj_mol: float = DEFAULT_EA_KJ_MOL,
    ) -> None:
        if ea_kj_mol <= 0:
            raise ValueError("Ea must be positive")

        self.ea_j_mol = ea_kj_mol * 1000.0

    def calculate(self, entries: Iterable[TemperatureEntry]) -> float:
        weights = []
        exponentials = []

        for entry in entries:
            duration_seconds = max(float(entry.duration_minutes), 1.0) * 60.0
            temp_k = float(entry.temperature) + 273.15
            if temp_k <= 0:
                continue
            weights.append(duration_seconds)
            exponentials.append(math.exp(-self.ea_j_mol / (R_J_MOL_K * temp_k)) * duration_seconds)

        if not weights or sum(weights) <= 0:
            return DEFAULT_REFERENCE_TEMP_C

        weighted_sum = sum(exponentials)
        total_time = sum(weights)

        try:
            mkt_k = -self.ea_j_mol / (R_J_MOL_K * math.log(weighted_sum / total_time))
        except (ValueError, ZeroDivisionError):
            return DEFAULT_REFERENCE_TEMP_C

        return mkt_k - 273.15
