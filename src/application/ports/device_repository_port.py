# src/application/ports/device_repository_port.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.thermal_record import ThermalRecord


class DeviceRepositoryPort(ABC):
    """
    Device-Centric repository contract.

    Provides immutable timeline retrieval for a single device.
    No filtering by time-range unless explicitly requested by higher layer.
    """

    @abstractmethod
    def get_device_history(self, device_id: str) -> List[ThermalRecord]:
        """
        Return full chronological thermal history for a device.

        Must return records ordered by timestamp ASC.
        Must not mutate domain entities.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_device_ids(self) -> List[str]:
        """
        Return distinct device identifiers available in storage.
        """
        raise NotImplementedError