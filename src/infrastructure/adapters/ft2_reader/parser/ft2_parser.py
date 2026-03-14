# src/infrastructure/adapters/ft2_reader/parser/ft2_parser.py

import csv
import warnings
from datetime import datetime
from typing import List

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class FT2Reading:
    """Lightweight object returned by FT2Parser for each timestamped reading.

    This class replaces the older ``FT2Entry`` name, which used to collide with
    the heavier domain entity.  ``FT2Reading`` intentionally has only the
    fields needed during parsing and early validation; downstream code that
    needs more semantic knowledge should convert to domain entities or DTOs.

    A compatibility alias is provided at the bottom of this module so that
    existing imports continue to work while emitting a deprecation warning.
    """

    def __init__(
        self,
        device_id: str,
        timestamp: datetime,
        temperature: float,
        vaccine_type: str,
        batch: str,
        duration_minutes: float = 15.0,
    ):
        self.device_id = device_id
        self.timestamp = timestamp
        self.temperature = temperature
        self.vaccine_type = vaccine_type
        self.batch = batch
        self.duration_minutes = duration_minutes

    def __repr__(self):
        return f"FT2Reading(device={self.device_id}, temp={self.temperature}°C, time={self.timestamp})"


class FT2Parser:
    @staticmethod
    def parse_file(file_path: str) -> List["FT2Reading"]:
        entries = []

        # دعم لكل من CSV و TSV
        delimiter = "\t" if file_path.endswith(".tsv") else ","

        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                # محاولة اكتشاف الرأس
                first_line = f.readline()
                f.seek(0)

                if "device_id" in first_line and "temperature" in first_line:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    for i, row in enumerate(reader):
                        try:
                            # Parse timestamp properly
                            ts_str = row.get("timestamp")
                            if ts_str:
                                try:
                                    ts = datetime.fromisoformat(ts_str)
                                except ValueError:
                                    # Handle simple cases or assume ISO
                                    ts = datetime.now()  # Fallback or error logic
                            else:
                                ts = datetime.now()

                            entry = FT2Reading(
                                device_id=str(row["device_id"]),
                                timestamp=ts,
                                temperature=float(row["temperature"]),
                                vaccine_type=row.get("vaccine_type", "UNKNOWN"),
                                batch=row.get("batch", "UNKNOWN"),
                                duration_minutes=15.0,  # افتراض 15 دقيقة لكل قراءة في CSV
                            )
                            entries.append(entry)
                        except Exception as e:
                            logger.warning(f"تخطي صف {i} في {file_path}: {e}")
                else:
                    logger.warning(f"تنسيق غير معروف في {file_path}")

        except Exception as e:
            logger.error(f"خطأ في تحليل {file_path}: {e}")

        logger.info(f"تم تحليل {len(entries)} إدخال من {file_path}")
        return entries


# ---------------------------------------------------------------------------
# Compatibility shim
# ---------------------------------------------------------------------------

# preserve old name for external callers; emit warning at import time

class FT2Entry(FT2Reading):  # type: ignore
    """Deprecated alias kept for backward compatibility.

    Use :class:`FT2Reading` or domain entities instead.  This class will be
    removed in Phase 5.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "FT2Entry is deprecated, use FT2Reading or domain entities instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
