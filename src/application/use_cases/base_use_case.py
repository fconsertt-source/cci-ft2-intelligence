# src/application/use_cases/base_use_case.py
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseUseCase(ABC):
    """Base class for all Use Cases in the application layer.

    Provides a common interface and enforces the execute() method contract.
    Use Cases must be pure — no dependencies on infrastructure or presentation.
    """

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the use case logic.

        Must be implemented by concrete use cases.
        Should accept Request DTOs and return Response DTOs.
        """
        pass
