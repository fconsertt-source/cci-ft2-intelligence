# tests/unit/test_encrypted_license_repository.py
import os
import tempfile

from src.infrastructure.security.encrypted_license_repository import \
    EncryptedLicenseRepository


def test_save_load_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        license_path = os.path.join(tmpdir, "license.dat")
        repo = EncryptedLicenseRepository(license_path, fingerprint="test-fp")

        data = {
            "fingerprint": "test-fp",
            "expiry": "2026-12-31",
            "signature": "deadbeef",
        }
        repo.save(data)

        loaded = repo.load()
        assert loaded == data
