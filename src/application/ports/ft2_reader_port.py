# src/application/ports/ft2_reader_port.py
from __future__ import annotations

from pathlib import Path
from typing import Protocol, List

from src.application.dtos.ft2_entry_dto import FT2EntryDTO


class Ft2ReaderPort(Protocol):
    """
    Port for reading FT2 raw data and returning pure DTOs (no analysis/decision logic).
    Implementations must return raw entries only — analysis happens in Use Cases.
    """
    def read(self, source: Path) -> List[FT2EntryDTO]:
        ...