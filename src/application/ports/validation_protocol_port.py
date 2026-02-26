from __future__ import annotations

from abc import ABC, abstractmethod


class ValidationProtocolPort(ABC):
    """
    Port for validation protocols.
    Enforces mandatory validation for PARTIAL status.
    """
    
    @abstractmethod
    def get_protocol(self, vaccine_type: str) -> dict:
        """
        Returns: validation protocol for vaccine type.
        """
        raise NotImplementedError
