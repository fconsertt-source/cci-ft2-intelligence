# src/application/ports/i_pdf_report_generator.py
from abc import ABC, abstractmethod
from typing import Optional

from src.application.dtos.device_report_dto import DeviceReportDTO


class IPDFReportGenerator(ABC):
    """Port for PDF report generation services."""

    @abstractmethod
    def generate_device_report_pdf(
        self,
        dto: DeviceReportDTO,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF report from DeviceReportDTO.

        Args:
            dto: Device report data transfer object.
            report_type: Type of report ('official', 'technical', 'arabic').
            language: Language code ('ar', 'en').
            filename: Optional filename for file output.

        Returns:
            PDF bytes if filename is None, else file path.
        """
        pass

    @abstractmethod
    def generate_center_report_pdf(
        self,
        center_data: dict,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF report for center summary.

        Args:
            center_data: Center report data.
            report_type: Type of report.
            language: Language code.
            filename: Optional filename.

        Returns:
            PDF bytes or file path.
        """
        pass