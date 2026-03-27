# src/infrastructure/security/encrypted_license_repository.py
from __future__ import annotations

import json
import os
from typing import Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class EncryptedLicenseRepository:
    def __init__(self, license_path: str, fingerprint: str):
        self._license_path = license_path
        self._fingerprint = fingerprint

    def _derive_key(self) -> bytes:
        # HKDF(fingerprint, info="cci-ft2-license-key")
        return HKDF(
            algorithm=SHA256(),
            length=32,
            salt=b"cci-ft2-salt",
            info=b"cci-ft2-license-key",
        ).derive(self._fingerprint.encode())

    def load(self) -> Optional[Dict]:
        if not os.path.exists(self._license_path):
            return None
        with open(self._license_path, "rb") as f:
            data = f.read()
        if len(data) < 12:  # nonce + tag
            return None
        nonce = data[:12]
        ciphertext = data[12:]
        key = self._derive_key()
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode())
        except Exception:
            return None

    def save(self, data: Dict) -> None:
        key = self._derive_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, json.dumps(data).encode(), None)
        with open(self._license_path, "wb") as f:
            f.write(nonce + ciphertext)
