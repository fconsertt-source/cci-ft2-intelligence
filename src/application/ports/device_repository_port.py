# src/application/ports/device_repository_port.py
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.domain.entities.thermal_record import ThermalRecord


class DeviceRepositoryPort(ABC):
    """
    Device-Centric repository contract.

    Provides immutable timeline retrieval for a single device, with optional
    time-range filtering.
    """

    @abstractmethod
    def get_device_history(
        self,
        device_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[ThermalRecord]:
        """
        Return chronological thermal history for a device.

        If date_from and/or date_to are provided, the history is filtered
        to that range.

        Must return records ordered by timestamp ASC.
        Must not mutate domain entities.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_device_ids(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[str]:
        """
        Return distinct device identifiers available in storage.

        If date_from and/or date_to are provided, this returns device_ids
        that have at least one record within that time range.
        """
        raise NotImplementedError
