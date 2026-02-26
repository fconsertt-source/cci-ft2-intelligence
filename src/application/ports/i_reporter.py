from __future__ import annotations
from typing import Protocol
from src.application.dtos.analysis_result_dto import AnalysisResultDTO

class IReporter(Protocol):
    """Port for reporting AnalysisResultDTO to various output formats.
    
    Implementations MUST live in infrastructure/adapters/.
    Application layer depends ONLY on this abstraction.
    """
    def generate(self, result: AnalysisResultDTO) -> None:
        """Generate output for a single analysis result."""
        raise NotImplementedError
