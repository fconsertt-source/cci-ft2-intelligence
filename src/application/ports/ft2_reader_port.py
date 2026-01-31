from __future__ import annotations

from pathlib import Path
from typing import Protocol

from application.dtos.analysis_result_dto import AnalysisResultDTO


class Ft2ReaderPort(Protocol):
    """
    Port for reading FT2 raw data and returning a DTO suitable for application layer consumption.
    Implementations live in infrastructure/adapters and must not be imported by application.
    """

    def read(self, source: Path) -> AnalysisResultDTO:  # Narrow DTO for app use
        """Read FT2 source (file or directory) and return structured DTO.
        Implementations may perform parsing/validation but must not leak domain entities.
        """
        ...
