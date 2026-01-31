from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.vaccine_dto import VaccineDTO


class IDataRepository(ABC):
    """Abstract data source for application. Returns DTOs only."""

    @abstractmethod
    def load_centers(self) -> Iterable[CenterDTO]:
        """Load centers as DTOs."""
        raise NotImplementedError

    @abstractmethod
    def load_vaccines(self) -> Iterable[VaccineDTO]:
        """Load vaccines as DTOs."""
        raise NotImplementedError
