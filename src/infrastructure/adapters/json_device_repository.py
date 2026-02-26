# src/infrastructure/adapters/json_device_repository.py
from datetime import datetime, timezone
import json
from typing import List
from src.domain.entities.thermal_record import ThermalRecord

class JsonDeviceRepository:
    def __init__(self, json_path: str):
        self._path = json_path

    def get_device_history(self, device_id: str) -> List[ThermalRecord]:
        """Return domain entities with FULL identity — ordered chronologically ASC."""
        with open(self._path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        device_records = [
            item for item in data
            if item.get('device_id') == device_id
        ]

        records = []
        for item in device_records:
            # ✅ تصحيح تنسيق التاريخ
            ts_str = item['timestamp']
            try:
                # Python 3.11+ supports 'Z' directly
                timestamp = datetime.fromisoformat(ts_str)
            except ValueError:
                # Fallback for older formats (e.g., "2025-01-01 00:00:00")
                timestamp = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')

            records.append(
                ThermalRecord(
                    device_id=item['device_id'],
                    timestamp=timestamp,
                    temperature=item['temperature'],
                    duration_minutes=item['duration_minutes'],
                    vaccine_type=item['vaccine_type']
                )
            )

        return sorted(records, key=lambda r: r.timestamp)