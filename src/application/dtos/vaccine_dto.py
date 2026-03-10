# re-export shim — Phase 5.2 (2026-03-10)
# @DEPRECATED: استخدم src.domain.dtos.vaccine_dto مباشرة
from src.domain.dtos.vaccine_dto import VaccineDTO  # noqa: F401

__all__ = ["VaccineDTO"]
