# src/application/use_cases/generate_device_report_uc_phase2.py
"""
Phase 2 Use Case for generating device reports.
"""
from typing import Dict, Any
from dataclasses import dataclass

from src.application.ports.i_report_generator import IReportGenerator
from src.application.ports.i_ledger_service import ILedgerService
from src.application.dtos.device_report_dto import DeviceReportDTO
from src.application.ports.performance_monitor_port import PerformanceMonitorPort


@dataclass
class GenerateDeviceReportRequest:
    """Request DTO for device report generation."""
    device_id: str
    center_name: str
    decision: str
    vvm_stage: str
    stability_budget_consumed_pct: float
    decision_reasons: list[str]
    language: str = "en"


@dataclass
class GenerateDeviceReportResponse:
    """Response DTO for device report generation."""
    success: bool
    file_path: str = ""
    hash: str = ""
    error_message: str = ""


class GenerateDeviceReportUCPhase2:
    """Phase 2 Use case for generating device reports."""

    def __init__(self, report_generator: IReportGenerator, ledger_service: ILedgerService, performance_monitor: PerformanceMonitorPort):
        self.report_generator = report_generator
        self.ledger_service = ledger_service
        self.performance_monitor = performance_monitor

    def execute(self, request: GenerateDeviceReportRequest) -> GenerateDeviceReportResponse:
        """Execute the device report generation use case."""
        with self.performance_monitor.measure(
            "generate_device_report",
            {"device_id": request.device_id, "language": request.language}
        ):
            try:
                # Convert request to DTO data
                dto_data = {
                    "device_id": request.device_id,
                    "center_name": request.center_name,
                    "decision": request.decision,
                    "vvm_stage": request.vvm_stage,
                    "stability_budget_consumed_pct": request.stability_budget_consumed_pct,
                    "decision_reasons": request.decision_reasons
                }

                # Generate report
                result = self.report_generator.generate_device_report(dto_data, request.language)

                # Record in ledger
                self.ledger_service.record_report_generation(
                    device_id=request.device_id,
                    report_type="device",
                    file_path=result["file_path"],
                    file_hash=result["hash"]
                )

                return GenerateDeviceReportResponse(
                    success=True,
                    file_path=result["file_path"],
                    hash=result["hash"]
                )

            except Exception as e:
                return GenerateDeviceReportResponse(
                    success=False,
                    error_message=str(e)
                )