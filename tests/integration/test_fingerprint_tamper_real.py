from datetime import datetime, timezone
from src.application.security.license_guard import LicenseGuard
from src.domain.policies.trial_policy import TrialPolicy
from src.infrastructure.security.fingerprint_provider import SystemFingerprintProvider
from src.application.security.license_validator import LicenseValidator
from src.infrastructure.security.encrypted_license_repository import EncryptedLicenseRepository

def _create_guard():
    class MockRepo:
        def load(self):
            return {
                "fingerprint": "A|B|C",
                "expiry": "2026-12-31T00:00:00Z",
                "install_time": "2025-01-01T00:00:00Z",
                "signature": "deadbeef"
            }
            
    return LicenseGuard(
        license_repo=MockRepo(),
        validator=LicenseValidator(),
        policy=TrialPolicy(
            installation_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            trial_duration_days=30,
            last_valid_run_time=None
        ),
        fingerprint_provider=SystemFingerprintProvider(),
        public_key_pem=b""
    )

def test_fingerprint_one_change_allowed():
    guard = _create_guard()
    # Simulate stored fingerprint: "A|B|C"
    # Current: "X|B|C" → one change → OK
    assert guard._fingerprint_tolerance_check("A|B|C", "X|B|C") is True

def test_fingerprint_two_changes_blocked():
    guard = _create_guard()
    assert guard._fingerprint_tolerance_check("A|B|C", "X|Y|C") is False