from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dtos.analysis_result_dto import AnalysisResultDTO


class IReporter(ABC):
    """Abstract reporter for generating artifacts from analysis results."""

    @abstractmethod
    def generate(self, result: AnalysisResultDTO) -> None:
        """Generate output for a single analysis result."""
        raise NotImplementedError
