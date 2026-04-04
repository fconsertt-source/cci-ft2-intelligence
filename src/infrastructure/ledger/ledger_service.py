# src/infrastructure/ledger/ledger_service.py
"""
Simple Ledger Service for Phase 2.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.application.ports.i_ledger_service import ILedgerService


class LedgerService(ILedgerService):
    """Simple file-based ledger service."""

    def __init__(self, ledger_file: str = None):
        self.ledger_file = Path(ledger_file or "data/ledger/phase2_ledger.jsonl")
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_file.exists():
            self.ledger_file.touch()

    def record_report_generation(self, device_id: str, report_type: str, file_path: str, file_hash: str) -> None:
        """Record report generation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "report_generated",
            "device_id": device_id,
            "report_type": report_type,
            "file_path": file_path,
            "file_hash": file_hash
        }
        self._append_entry(entry)

    def record_device_evaluation(self, device_id: str, decision: str, reasons: list[str]) -> None:
        """Record device evaluation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "device_evaluated",
            "device_id": device_id,
            "decision": decision,
            "reasons": reasons
        }
        self._append_entry(entry)

    def _append_entry(self, entry: Dict[str, Any]) -> None:
        """Append entry to ledger file."""
        with open(self.ledger_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')