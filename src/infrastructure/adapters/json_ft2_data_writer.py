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

    def write(self, destination: Path, data: List[FT2EntryDTO]) -> None:
        """Writes or appends a list of FT2EntryDTOs to a JSON file."""
        destination.parent.mkdir(parents=True, exist_ok=True)

        existing_entries = []
        if destination.exists():
            try:
                with open(destination, "r", encoding="utf-8") as f:
                    existing_entries = json.load(f)
            except Exception:
                existing_entries = []

        merged = {str(item.get("id")): item for item in existing_entries if isinstance(item, dict) and item.get("id")}
        for entry in data:
            merged[str(entry.id)] = asdict(entry)

        with open(destination, "w", encoding="utf-8") as f:
            json.dump(list(merged.values()), f, ensure_ascii=False, indent=2, default=str)
