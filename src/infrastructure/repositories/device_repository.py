from __future__ import annotations

"""Higher‑level repository implementation used by use‑cases and UI.

This class currently delegates to the JSON adapter, but the abstraction
makes it easier to swap out storage later without touching the callers.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from src.application.ports.device_repository_port import DeviceRepositoryPort
from src.infrastructure.adapters.json_device_repository import JsonDeviceRepository


class DeviceDataRepository(JsonDeviceRepository, DeviceRepositoryPort):
    """Concrete repository that satisfies ``DeviceRepositoryPort``.

    Defaults to the canonical `ft2_data.json` file in the project root but
    accepts a custom path for testing or alternative data sources.
    """

    def __init__(self, json_path: str | None = None) -> None:
        if json_path is None:
            json_path = "ft2_data.json"
        super().__init__(json_path=json_path)

    # ``JsonDeviceRepository`` implements ``get_device_history`` with date filtering.
    # We provide an implementation for ``get_all_device_ids`` here.

    def get_all_device_ids(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[str]:
        """Return distinct device identifiers, optionally filtered by time."""
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not date_from and not date_to:
            return sorted(
                {item.get("device_id") for item in data if item.get("device_id")}
            )

        # Normalize filter dates to timezone-aware UTC
        if date_from and date_from.tzinfo is None:
            date_from = date_from.replace(tzinfo=timezone.utc)
        if date_to and date_to.tzinfo is None:
            date_to = date_to.replace(tzinfo=timezone.utc)

        device_ids = set()
        for item in data:
            if not item.get("device_id"):
                continue

            ts_str = item["timestamp"]
            try:
                timestamp = datetime.fromisoformat(ts_str)
            except (ValueError, KeyError):
                # Fallback for older formats or missing timestamp
                try:
                    timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except (ValueError, KeyError):
                    continue  # Skip records with unparsable dates

            # Normalize record timestamp to timezone-aware UTC
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Apply date filtering
            if date_from and timestamp < date_from:
                continue
            if date_to and timestamp > date_to:
                continue

            device_ids.add(item.get("device_id"))

        return sorted(list(device_ids))
