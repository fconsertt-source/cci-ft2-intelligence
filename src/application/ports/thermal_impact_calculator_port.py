from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.vaccine_specification import VaccineSpecification


class ThermalImpactCalculatorPort(ABC):
    """
    Port for evaluating thermal impact on vaccines.
    Follows same pattern as Ft2ReaderPort in Phase 5.
    """

    @abstractmethod
    def evaluate(
        self,
        temperature: float,
        duration_minutes: float,
        specification: VaccineSpecification,
    ) -> str:  # Returns "SAFE", "PARTIAL", or "DISCARD"
        """
        Evaluate thermal impact based on temperature and duration.
        """
        raise NotImplementedError
