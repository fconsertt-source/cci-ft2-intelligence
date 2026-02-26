from pathlib import Path
from typing import Protocol

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.domain.ledger.events import LedgerEvent


class RecordVerificationUseCase:
    """Use case for recording verification events in the ledger"""
    
    def __init__(self, ledger_writer: LedgerWriterPort):
        self.ledger_writer = ledger_writer
    
    def record_ingestion(self, file_hash: str, file_path: Path, ft2_serial: str) -> str:
        """Record file ingestion event"""
        entry = self.ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash=file_hash,
            ft2_serial=ft2_serial,
            source_path=str(file_path)
        )
        return entry.event_id
    
    def record_authenticity_result(
        self,
        file_hash: str,
        ft2_serial: str,
        is_valid: bool,
        alarm_detected: bool,
        diagnostics: str
    ) -> str:
        """Record authenticity verification result"""
        event_type = (
            LedgerEvent.AUTHENTICITY_VERIFIED if is_valid 
            else LedgerEvent.AUTHENTICITY_FAILED
        )
        
        entry = self.ledger_writer.append(
            event_type=event_type,
            file_hash=file_hash,
            ft2_serial=ft2_serial,
            authenticity_status="VALID" if is_valid else "INVALID",
            alarm_detected=alarm_detected,
            metadata={"diagnostics": diagnostics}
        )
        return entry.event_id
    
    def record_final_verdict(
        self,
        file_hash: str,
        asset_id: str,
        verdict: str,  # "SAFE", "PARTIAL", "DISCARD"
        destination_path: Path
    ) -> str:
        """Record final verdict and routing decision"""
        event_map = {
            "SAFE": LedgerEvent.FINAL_VERDICT_SAFE,
            "PARTIAL": LedgerEvent.FINAL_VERDICT_PARTIAL,
            "DISCARD": LedgerEvent.FINAL_VERDICT_DISCARD,
        }
        
        entry = self.ledger_writer.append(
            event_type=event_map[verdict],
            file_hash=file_hash,
            asset_id=asset_id,
            destination_path=str(destination_path)
        )
        return entry.event_id