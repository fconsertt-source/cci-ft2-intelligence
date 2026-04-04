"""Domain port for thermal impact calculation."""
from abc import ABC, abstractmethod
from typing import List
from src.domain.value_objects.temperature_entry import TemperatureEntry


class ThermalCalculatorPort(ABC):
    """Pure domain interface for HET/Q10 thermal impact calculation."""

    @abstractmethod
    def calculate_q10_impact(self, entries: List[TemperatureEntry], reference_temp: float) -> float:
        """Calculate cumulative Q10 impact factor. """
        pass

    @abstractmethod
    def evaluate(self, temperature: float, duration_minutes: float, reference_temp: float) -> str:
        """Evaluate sample state as SAFE/PARTIAL/DISCARD."""
        pass
