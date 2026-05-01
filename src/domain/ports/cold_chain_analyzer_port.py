from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.value_objects.cold_chain_analysis_result import ColdChainAnalysisResult


class ColdChainAnalyzerPort(ABC):
    """Domain port for cold chain continuity analysis."""

    @abstractmethod
    def analyze(self, records: List[ThermalRecord]) -> ColdChainAnalysisResult:
        ...
