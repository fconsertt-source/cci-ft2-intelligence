"""Domain enums — controlled vocabularies."""

from .vaccine_decision import DecisionReason, VaccineDecision
# إعادة تصدير الـ Enums المستخدمة في DeviceReportDTO
from src.application.dtos.device_report_dto import ReportDecision, VVMStage

__all__ = ["DecisionReason", "VaccineDecision", "ReportDecision", "VVMStage"]