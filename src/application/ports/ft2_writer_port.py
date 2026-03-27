from __future__ import annotations

from pathlib import Path
from typing import List, Protocol

from src.domain.dtos.ft2_entry_dto import FT2EntryDTO


class Ft2WriterPort(Protocol):
    """
    Port for writing FT2 data to a specified output path.
    """

    def write(self, destination: Path, data: List[FT2EntryDTO]) -> None: ...
