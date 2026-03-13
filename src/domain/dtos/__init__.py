"""
Domain DTOs - كائنات نقل البيانات التجارية
✅ تمثل مفاهيم أعمال (Ubiquitous Language)
✅ تُستخدم عبر جميع الطبقات
✅ مستقلة عن Use Cases محددة
"""

from .analysis_result_dto import AnalysisResultDTO, VaccineStatus
from .base_dto import BaseDTO
from .center_dto import CenterDTO
from .device_report_dto import (
    AdvisorySection,
    DeviceReportDTO,
    ThermalExcursionDTO,
    ValidationProtocol,
)
from .evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest,
    TemperatureReading,
)
from .ft2_entry_dto import FT2EntryDTO
from .report_input_dto import ReportInputDTO
from .vaccine_dto import VaccineDTO

__all__ = [
    "AnalysisResultDTO",
    "VaccineStatus",
    "BaseDTO",
    "CenterDTO",
    "DeviceReportDTO",
    "ThermalExcursionDTO",
    "AdvisorySection",
    "ValidationProtocol",
    "EvaluateColdChainSafetyRequest",
    "TemperatureReading",
    "FT2EntryDTO",
    "ReportInputDTO",
    "VaccineDTO",
]
