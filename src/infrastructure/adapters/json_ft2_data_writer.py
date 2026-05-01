# src/infrastructure/adapters/json_ft2_data_writer.py
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from src.application.ports.ft2_writer_port import Ft2WriterPort
from src.application.dtos.ft2_entry_dto import FT2EntryDTO


class JsonFt2DataWriter(Ft2WriterPort):
    """Writes a list of FT2EntryDTOs to a JSON file."""

    def write(self, data: List[FT2EntryDTO], destination: Path) -> None:
        """Writes a list of FT2EntryDTOs to a JSON file."""
        # ✅ الترتيب: data (القائمة) أولاً، ثم destination (المسار)
        dto_list = [asdict(entry) for entry in data]

        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, "w", encoding="utf-8") as f:
            json.dump(dto_list, f, ensure_ascii=False, indent=2, default=str)
