# src/application/ports/i_report_generator.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class IReportGenerator(ABC):
    """Port for report generation services."""

    @abstractmethod
    def generate_device_report(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Generate device report.

        Args:
            data: Report data including device info, readings, decisions.
            language: 'ar' or 'en'.

        Returns:
            Dict with 'file_path' and 'hash'.
        """
        pass

    @abstractmethod
    def generate_center_report(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Generate center report.

        Args:
            data: Report data including center info, devices, summary.
            language: 'ar' or 'en'.

        Returns:
            Dict with 'file_path' and 'hash'.
        """
        pass