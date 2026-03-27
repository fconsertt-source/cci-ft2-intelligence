# src/application/ports/text_signature_verifier_port.py
from __future__ import annotations

from typing import Protocol

from src.domain.evidence.verification_result import VerificationResult


class ITextSignatureVerifier(Protocol):
    def verify(self, raw_content: bytes) -> VerificationResult: ...
