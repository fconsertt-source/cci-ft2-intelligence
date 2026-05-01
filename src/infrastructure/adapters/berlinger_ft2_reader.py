from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List

from src.application.ports.ft2_reader_port import Ft2ReaderPort
from src.application.dtos.ft2_entry_dto import FT2EntryDTO

logger = logging.getLogger(__name__)


class BerlingerFt2Reader(Ft2ReaderPort):
    """Adapter for Berlinger Fridge-tag® 2 E format — implements Ft2ReaderPort.

    Handles both single files and directories (processes all .txt files).
    Extracts hierarchical context:
      - device_id: from Serial field in file content
      - batch_id: from filename pattern (e.g., OPV_batch_123.txt)
      - center_id: from parent directory name
    """

    def read(self, source: str) -> List[FT2EntryDTO]:
        """Read FT2 data from a file path or directory."""
        path = Path(source)

        # ✅ Support directories: process all .txt files
        if path.is_dir():
            entries = []
            for file_path in path.glob("*.txt"):
                entries.extend(self._parse_single_file(file_path))
            return entries

        # ✅ Support single files
        return self._parse_single_file(path)

    def _parse_single_file(self, path: Path) -> List[FT2EntryDTO]:
        """Parse a single Berlinger FT2 file."""
        if not self._is_berlinger_format(path):
            return []

        try:
            return self._parse_berlinger(path)
        except Exception:
            return []

    def _is_berlinger_format(self, path: Path) -> bool:
        """Detect Berlinger Fridge-tag 2 E format by checking the file header."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                hist_found = False
                fridgetag_found = False
                alarm_found = False
                loc_found = False

                for i, line in enumerate(f):
                    if i >= 50:
                        break
                    lower = line.lower()
                    if "hist:" in lower:
                        hist_found = True
                    if "fridge-tag 2 e" in lower or "q-tag fridge-tag 2 e" in lower:
                        fridgetag_found = True
                    if "alarm" in lower:
                        alarm_found = True
                    if "loc:" in lower or "location:" in lower:
                        loc_found = True

                if hist_found and fridgetag_found and alarm_found and loc_found:
                    return True

            logger.warning(
                "Skipping %s: not compliant with Fridge-tag 2E PQS E006-TR07 requirements "
                "(hist=%s, device=%s, alarm=%s, loc=%s)",
                path,
                hist_found,
                fridgetag_found,
                alarm_found,
                loc_found,
            )
            return False
        except Exception:
            return False

    def _parse_berlinger(self, path: Path) -> List[FT2EntryDTO]:
        """Parse Berlinger format with line-by-line state machine."""
        entries = []

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # 1. Extract device_id from Serial field (first 30 lines)
        device_id = "UNKNOWN"
        for line in lines[:30]:
            serial_match = re.search(r"Serial:\s*(\d{12})", line)
            if serial_match:
                device_id = serial_match.group(1)
                break

        # 2. Extract batch_id from filename (e.g., OPV_batch_123.txt → OPV_batch_123)
        batch_id = self._extract_batch_id(path.name)

        # 3. Extract center_id from parent directory name
        center_id = path.parent.name if path.parent.name != "input_ft2" else "UNKNOWN"

        # 4. Parse daily entries with state machine
        in_hist_section = False
        current_date = None
        current_avg_temp = None

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if "Hist:" in stripped:
                in_hist_section = True
                continue

            if not in_hist_section:
                continue

            if stripped.startswith("TS "):
                continue

            if re.match(r"^\d+:$", stripped):
                if current_date and current_avg_temp:
                    try:
                        timestamp = datetime.fromisoformat(current_date)
                        temp_clean = current_avg_temp.lstrip("+")
                        temperature = float(temp_clean)

                        entries.append(
                            FT2EntryDTO(
                                id=f"{device_id}_{timestamp.isoformat()}",
                                device_id=device_id,
                                timestamp=timestamp,
                                temperature=temperature,
                                vaccine_type="General",
                                batch="BATCH_UNKNOWN",
                                duration_minutes=1440.0,
                                batch_id=batch_id,  # ← New field
                                center_id=center_id,  # ← New field
                            )
                        )
                    except (ValueError, TypeError):
                        pass
                current_date = None
                current_avg_temp = None
                continue

            if "date:" in stripped.lower():
                date_match = re.search(
                    r"date:\s*(\d{4}-\d{2}-\d{2})", stripped, re.IGNORECASE
                )
                if date_match:
                    current_date = date_match.group(1)
                continue

            if "avrg t:" in stripped.lower():
                temp_match = re.search(
                    r"avrg\s*t:\s*([+-]?\d+\.?\d*)", stripped, re.IGNORECASE
                )
                if temp_match:
                    current_avg_temp = temp_match.group(1)
                continue

        # Save last entry if complete
        if current_date and current_avg_temp:
            try:
                timestamp = datetime.fromisoformat(current_date)
                temp_clean = current_avg_temp.lstrip("+")
                temperature = float(temp_clean)
                entries.append(
                    FT2EntryDTO(
                        id=f"{device_id}_{timestamp.isoformat()}",
                        device_id=device_id,
                        timestamp=timestamp,
                        temperature=temperature,
                        vaccine_type="General",
                        batch="BATCH_UNKNOWN",
                        duration_minutes=1440.0,
                        batch_id=batch_id,  # ← New field
                        center_id=center_id,  # ← New field
                    )
                )
            except (ValueError, TypeError):
                pass

        return entries[-7:] if len(entries) > 7 else entries

    def _extract_batch_id(self, filename: str) -> str:
        """Extract batch_id from filename (e.g., OPV_batch_123.txt → OPV_batch_123)."""
        # Simple extraction: remove extension and normalize
        batch_id = filename.rsplit(".", 1)[0] if "." in filename else filename
        # Optional: extract only alphanumeric parts (e.g., "OPV_batch_123" → "OPV_batch_123")
        return batch_id
