# src/application/use_cases/generate_pdf_report_uc.py
"""Generate PDF Report Use Case — Clean Architecture compliant."""

from __future__ import annotations

from typing import Optional

from src.application.dtos.device_report_dto import DeviceReportDTO
from src.application.ports.i_pdf_report_generator import IPDFReportGenerator


class GeneratePDFReportUseCase:
    """Use Case for generating PDF reports from DTOs."""

    def __init__(self, pdf_generator: IPDFReportGenerator):
        self._pdf_generator = pdf_generator

    def execute_device_report(
        self,
        dto: DeviceReportDTO,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None
    ) -> bytes:
        """
        Execute PDF generation for device report.

        Args:
            dto: Device report DTO.
            report_type: Report type.
            language: Language code.
            filename: Optional filename.

        Returns:
            PDF bytes.
        """
        return self._pdf_generator.generate_device_report_pdf(
            dto=dto,
            report_type=report_type,
            language=language,
            filename=filename
        )

    def execute_center_report(
        self,
        center_data: dict,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None
    ) -> bytes:
        """
        Execute PDF generation for center report.

        Args:
            center_data: Center data dictionary.
            report_type: Report type.
            language: Language code.
            filename: Optional filename.

        Returns:
            PDF bytes.
        """
        return self._pdf_generator.generate_center_report_pdf(
            center_data=center_data,
            report_type=report_type,
            language=language,
            filename=filename
        )