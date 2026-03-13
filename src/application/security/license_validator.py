# src/application/security/license_validator.py
from __future__ import annotations
from typing import Protocol
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

class LicenseValidatorProtocol(Protocol):
    def verify_signature(self, data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
        ...

class LicenseValidator(LicenseValidatorProtocol):
    def verify_signature(self, data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
        try:
            key = load_pem_public_key(public_key_pem)
            key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False