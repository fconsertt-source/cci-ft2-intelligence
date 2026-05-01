# src/application/use_cases/generate_center_report_uc_phase2.py
"""
Phase 2 Use Case for generating center reports.
"""
from typing import Dict, Any
from dataclasses import dataclass

from src.application.ports.i_report_generator import IReportGenerator
from src.application.ports.i_ledger_service import ILedgerService
from src.application.ports.performance_monitor_port import PerformanceMonitorPort
from src.domain.exceptions import BaseSystemException


@dataclass
class GenerateCenterReportRequest:
    """Request DTO for center report generation."""
    center_id: str
    center_name: str
    total_devices: int
    safe_devices: int
    rejected_devices: int
    partial_devices: int
    language: str = "en"


@dataclass
class GenerateCenterReportResponse:
    """Response DTO for center report generation."""
    success: bool
    file_path: str = ""
    hash: str = ""
    error_message: str = ""


class GenerateCenterReportUCPhase2:
    """Phase 2 Use case for generating center reports."""

    def __init__(self, report_generator: IReportGenerator, ledger_service: ILedgerService, performance_monitor: PerformanceMonitorPort):
        self.report_generator = report_generator
        self.ledger_service = ledger_service
        self.performance_monitor = performance_monitor

    def execute(self, request: GenerateCenterReportRequest) -> GenerateCenterReportResponse:
        """Execute the center report generation use case."""
        with self.performance_monitor.measure(
            "generate_center_report",
            {"center_id": request.center_id, "language": request.language}
        ):
            try:
                # Convert request to DTO data
                dto_data = {
                    "center_id": request.center_id,
                    "center_name": request.center_name,
                    "total_devices": request.total_devices,
                    "safe_devices": request.safe_devices,
                    "rejected_devices": request.rejected_devices,
                    "partial_devices": request.partial_devices
                }

                # Generate report
                result = self.report_generator.generate_center_report(dto_data, request.language)

                # Record in ledger
                self.ledger_service.record_report_generation(
                    device_id=f"center_{request.center_id}",
                    report_type="center",
                    file_path=result["file_path"],
                    file_hash=result["hash"]
                )

                return GenerateCenterReportResponse(
                    success=True,
                    file_path=result["file_path"],
                    hash=result["hash"]
                )

            except BaseSystemException as e:
                return GenerateCenterReportResponse(
                    success=False,
                    error_message=e.user_message,
                )