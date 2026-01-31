from __future__ import annotations

from src.application.ports.i_reporter import IReporter
from src.application.dtos.analysis_result_dto import AnalysisResultDTO


class NoOpReporter(IReporter):
    """A no-op reporter implementation for wiring verification."""

    def generate(self, result: AnalysisResultDTO) -> None:  # pragma: no cover - trivial
        # Intentionally do nothing; acts as a placeholder reporter.
        return None
