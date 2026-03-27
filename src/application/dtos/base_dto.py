# re-export shim — Phase 5.2 (2026-03-10)
# @DEPRECATED: استخدم src.domain.dtos.base_dto مباشرة
from src.domain.dtos.base_dto import BaseDTO  # noqa: F401

__all__ = ["BaseDTO"]
