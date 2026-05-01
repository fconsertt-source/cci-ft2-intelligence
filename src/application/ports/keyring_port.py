# src/application/ports/keyring_port.py
from __future__ import annotations

from typing import Optional, Protocol


class PublicKeyRecord(Protocol):
    issuer: str
    algorithm: str  # e.g. RSASSA-PKCS1-v1_5
    hash_name: str  # e.g. SHA-256
    public_key_pem: bytes
    key_status: str  # active / revoked / expired


class KeyRingPort(Protocol):
    def get_key(self, issuer: str) -> Optional[PublicKeyRecord]: ...
