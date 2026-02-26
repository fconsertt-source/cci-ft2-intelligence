# tests/unit/application/security/test_text_signature_verifier.py

import pytest

from src.domain.evidence.verification_result import VerificationStatus, VerificationResult
from src.infrastructure.security.text_signature_verifier import TextSignatureVerifier


class DummyKeyRecord:
    def __init__(self, issuer: str, public_key_pem: bytes):
        self.issuer = issuer
        self.algorithm = "RSASSA-PKCS1-v1_5"
        self.hash_name = "SHA-256"
        self.public_key_pem = public_key_pem
        self.key_status = "active"


class DummyKeyRing:
    def __init__(self, key_record):
        self._key_record = key_record

    def get_key(self, issuer: str):
        if issuer == self._key_record.issuer:
            return self._key_record
        return None


@pytest.fixture
def verifier(sample_public_key_pem):
    key_record = DummyKeyRecord(
        issuer="Berlinger & Co. AG",
        public_key_pem=sample_public_key_pem,
    )
    keyring = DummyKeyRing(key_record)
    return TextSignatureVerifier(keyring)


def test_signature_missing(verifier):
    raw = b"Device: X\nTemp: 5.0\n"
    result = verifier.verify(raw)
    assert result.status == VerificationStatus.SIGNATURE_MISSING
    
@pytest.fixture
def sample_public_key_pem():
    """Minimal RSA public key for testing."""
    return b"""-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALeFakeKeyForTestsOnlyDontUseInProd
FakeFakeFakeFakeFakeFakeFakeFakeFakeFakeFakeFakeFakeIDAQAB
-----END PUBLIC KEY-----"""