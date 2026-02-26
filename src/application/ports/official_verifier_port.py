from __future__ import annotations
from typing import Protocol
from pathlib import Path
from src.domain.evidence.verification_result import VerificationResult


class OfficialVerifierPort(Protocol):
    """
    Port for invoking official external verification (e.g., Berlinger JAR).
    """

    def verify_file(self, file_path: Path):
        """
        Verify a file using the official verifier.
        
        Args:
            file_path: Path to the TXT or PDF file to verify.
            
        Returns:
            VerificationResult domain object.
        """
        ...
