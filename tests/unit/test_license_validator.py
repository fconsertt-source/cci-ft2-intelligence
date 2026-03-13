# tests/unit/test_license_validator.py
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from src.application.security.license_validator import LicenseValidator

def test_valid_signature():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    data = b"test-data"
    signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))

    validator = LicenseValidator()
    assert validator.verify_signature(data, signature, public_pem) is True

def test_invalid_signature():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    data = b"test-data"
    signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
    invalid_sig = signature[:-1] + bytes([signature[-1] ^ 0xFF])  # corrupt last byte

    validator = LicenseValidator()
    assert validator.verify_signature(data, invalid_sig, public_pem) is False