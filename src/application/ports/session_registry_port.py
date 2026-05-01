from datetime import datetime
from typing import Protocol


class SessionRegistryPort(Protocol):
    def is_new_data(self, device_id: str, file_timestamp: datetime) -> bool:
        """Return True when this file timestamp has not been processed."""
        ...

    def mark_processed(
        self,
        device_id: str,
        last_timestamp: datetime,
        filename: str,
        readings_count: int,
    ) -> None:
        """Record the last processed file for a device."""
        ...
