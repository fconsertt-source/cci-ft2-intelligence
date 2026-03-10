# re-export shim — Phase 5.2 (2026-03-10)
# @DEPRECATED: استخدم src.domain.dtos.report_input_dto مباشرة
from src.domain.dtos.report_input_dto import (  # noqa: F401
    ReportInputDTO,
    make_immutable,
)

__all__ = ["ReportInputDTO", "make_immutable"]
