# src/application/ports/i_license_guard.py
from abc import ABC, abstractmethod


class ILicenseGuard(ABC):
    """
    Port for license validation services.
    """
    @abstractmethod
    def ensure_active(self) -> None:
        """Ensures the application license is active, raising an exception if not."""