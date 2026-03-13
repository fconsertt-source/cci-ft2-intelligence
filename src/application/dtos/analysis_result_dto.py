# re-export shim — Phase 5.2 (2026-03-10)
# @DEPRECATED: استخدم src.domain.dtos.analysis_result_dto مباشرة
from src.domain.dtos.analysis_result_dto import (  # noqa: F401
    AnalysisResultDTO,
    VaccineStatus,
)

__all__ = ["AnalysisResultDTO", "VaccineStatus"]
