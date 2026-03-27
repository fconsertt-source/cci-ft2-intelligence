# src/application/ports/thermal_degradation_estimator_port.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class ThermalDegradationEstimatorPort(ABC):
    """
    Provides SCIENTIFIC ESTIMATES only.
    NEVER influences decision path.
    """

    @abstractmethod
    def estimate_remaining_potency(
        self, thermal_history: List[ThermalRecord], spec: VaccineSpecification
    ) -> float:
        """
        Returns: estimated remaining potency percentage (0.0 - 100.0)
        For ADVISORY purposes only.
        """
        raise NotImplementedError

    @abstractmethod
    def calculate_cumulative_impact(
        self, thermal_history: List[ThermalRecord], spec: VaccineSpecification
    ) -> Dict:
        """
        Returns: detailed cumulative impact analysis
        For ADVISORY purposes only.
        """
        raise NotImplementedError
