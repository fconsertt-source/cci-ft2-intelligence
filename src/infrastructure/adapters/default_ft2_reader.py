import os
import uuid
from pathlib import Path
from typing import List

from src.domain.dtos.ft2_entry_dto import FT2EntryDTO
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import \
    FT2Reading as FT2Entry


class DefaultFt2Reader:
    """
    Adapter that implements the Ft2ReaderPort to read data from a directory of FT2 files.
    """

    def read(self, source: Path) -> List[FT2EntryDTO]:
        """
        Reads all .txt files in a source directory, parses them, and returns a list of FT2EntryDTOs.
        """
        all_entries: List[FT2Entry] = []
        if not source.is_dir():
            # In the future, we might support single file reads.
            # For now, align with the CLI contract.
            return []

        for filename in os.listdir(source):
            if filename.endswith(".txt"):
                file_path = source / filename
                entries = FT2Parser.parse_file(str(file_path))
                all_entries.extend(entries)

        # Convert domain-like entries to pure DTOs
        dto_list = [
            FT2EntryDTO(
                id=str(uuid.uuid4()),
                device_id=entry.device_id,
                timestamp=entry.timestamp,
                temperature=entry.temperature,
                vaccine_type=entry.vaccine_type,
                batch=entry.batch,
                duration_minutes=entry.duration_minutes,
            )
            for entry in all_entries
        ]

        return dto_list
