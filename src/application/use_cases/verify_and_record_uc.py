import hashlib
import uuid
from pathlib import Path
from typing import Optional

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.application.ports.official_verifier_port import OfficialVerifierPort
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.evidence.verification_result import (
    VerificationResult,
    VerificationStatus,
)


class VerifyAndRecordUseCase:
    """
    Use Case: Orchestrates the official verification of a file and records the
    outcome in the forensic ledger.
    """

    def __init__(self, verifier: OfficialVerifierPort, ledger: LedgerWriterPort):
        self.verifier = verifier
        self.ledger = ledger

    def execute(self, file_path: Path) -> VerificationResult:
        # 1. Perform Official Verification
        result = self.verifier.verify_file(file_path)

        # 2. Calculate File Hash (SHA-256) for the ledger record
        file_hash = self._calculate_file_hash(file_path)

        # 3. Determine Event Type
        # We consider SUCCESS as verified. Any other status is a failure of authenticity/integrity.
        is_verified = result.status == VerificationStatus.SUCCESS
        event_type = (
            LedgerEvent.AUTHENTICITY_VERIFIED
            if is_verified
            else LedgerEvent.AUTHENTICITY_FAILED
        )

        # 4. Record in Ledger
        self.ledger.append(
            event_type=event_type,
            file_hash=file_hash,
            event_id=str(uuid.uuid4()),
            authenticity_status=result.status.value,
            source_path=str(file_path),
        )

        return result

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculates SHA-256 hash of the file content."""
        if not file_path.exists():
            return "FILE_NOT_FOUND"

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
