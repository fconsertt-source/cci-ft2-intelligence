# src/infrastructure/adapters/json_device_repository.py
import json
from datetime import datetime, timezone
from typing import List, Optional

from src.domain.entities.thermal_record import ThermalRecord


class JsonDeviceRepository:
    def __init__(self, json_path: str):
        self._path = json_path

    def get_device_history(
        self,
        device_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[ThermalRecord]:
        """Return domain entities with FULL identity — ordered chronologically ASC."""
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        device_records = [item for item in data if item.get("device_id") == device_id]

        # Normalize filter dates to timezone-aware UTC
        if date_from and date_from.tzinfo is None:
            date_from = date_from.replace(tzinfo=timezone.utc)
        if date_to and date_to.tzinfo is None:
            date_to = date_to.replace(tzinfo=timezone.utc)

        records = []
        for item in device_records:
            # ✅ تصحيح تنسيق التاريخ
            ts_str = item["timestamp"]
            try:
                # Python 3.11+ supports 'Z' directly
                timestamp = datetime.fromisoformat(ts_str)
            except ValueError:
                # Fallback for older formats (e.g., "2025-01-01 00:00:00")
                timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

            # Normalize record timestamp to timezone-aware UTC
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Apply date filtering
            if date_from and timestamp < date_from:
                continue
            if date_to and timestamp > date_to:
                continue

            records.append(
                ThermalRecord(
                    device_id=item["device_id"],
                    timestamp=timestamp,
                    temperature=item["temperature"],
                    duration_minutes=item["duration_minutes"],
                    vaccine_type=item["vaccine_type"],
                )
            )

        return sorted(records, key=lambda r: r.timestamp)
