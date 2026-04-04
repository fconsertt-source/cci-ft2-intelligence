# src/application/ports/i_ledger_service.py
"""
Ledger Service Port for Phase 2.
"""
from abc import ABC, abstractmethod
from typing import Protocol


class ILedgerService(Protocol):
    """Port for ledger operations in Phase 2."""

    @abstractmethod
    def record_report_generation(self, device_id: str, report_type: str, file_path: str, file_hash: str) -> None:
        """Record report generation in ledger."""
        pass

    @abstractmethod
    def record_device_evaluation(self, device_id: str, decision: str, reasons: list[str]) -> None:
        """Record device evaluation in ledger."""
        pass