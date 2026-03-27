# src/domain/evidence/verification_result.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VerificationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    CRYPTO_FAILURE = "CRYPTO_FAILURE"
    MALFORMED_STRUCTURE = "MALFORMED_STRUCTURE"
    UNTRUSTED_ISSUER = "UNTRUSTED_ISSUER"
    SIGNATURE_MISSING = "SIGNATURE_MISSING"
    DECODE_ERROR = "DECODE_ERROR"
    SIZE_LIMIT_EXCEEDED = "SIZE_LIMIT_EXCEEDED"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    issuer: Optional[str] = None
    normalized_data: Optional[bytes] = None
    signature_hex: Optional[str] = None
    diagnostics: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == VerificationStatus.SUCCESS
