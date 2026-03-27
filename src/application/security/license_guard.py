from __future__ import annotations

import json
from datetime import datetime, timezone

from src.application.security.license_validator import LicenseValidator
from src.domain.policies.trial_policy import TrialPolicy, TrialStatus
from src.infrastructure.security.encrypted_license_repository import \
    EncryptedLicenseRepository
from src.infrastructure.security.fingerprint_provider import \
    SystemFingerprintProvider


class LicenseExpiredError(Exception):
    pass


class IntegrityError(Exception):
    pass


class LicenseGuard:
    def __init__(
        self,
        license_repo: EncryptedLicenseRepository,
        validator: LicenseValidator,
        policy: TrialPolicy,
        fingerprint_provider: SystemFingerprintProvider,
        public_key_pem: bytes,
    ):
        self._repo = license_repo
        self._validator = validator
        self._policy = policy
        self._fingerprint_provider = fingerprint_provider
        self._public_key_pem = public_key_pem

    def _fingerprint_tolerance_check(self, stored: str, current: str) -> bool:
        """Allow at most one component to differ."""
        stored_parts = stored.split("|")
        current_parts = current.split("|")
        if len(stored_parts) != len(current_parts):
            return False
        diff_count = sum(1 for s, c in zip(stored_parts, current_parts) if s != c)
        return diff_count <= 1

    def ensure_active(self) -> None:
        # 1. Load license
        license_data = self._repo.load()
        if not license_data:
            raise IntegrityError("License file missing or corrupted")

        # 2. Verify signature
        data_to_verify = json.dumps(
            {
                "fingerprint": license_data["fingerprint"],
                "expiry": license_data["expiry"],
                "install_time": license_data["install_time"],
            },
            sort_keys=True,
        ).encode()
        sig = bytes.fromhex(license_data["signature"])
        if not self._validator.verify_signature(
            data_to_verify, sig, self._public_key_pem
        ):
            raise IntegrityError("Invalid license signature")

        # 3. Verify fingerprint (tolerance: 1 change allowed)
        current_fingerprint = "|".join(
            [
                self._fingerprint_provider.get_machine_id(),
                self._fingerprint_provider.get_os_uuid(),
                self._fingerprint_provider.get_install_timestamp(),
            ]
        )
        stored_fingerprint = license_data["fingerprint"]

        if not self._fingerprint_tolerance_check(
            stored_fingerprint, current_fingerprint
        ):
            raise IntegrityError(
                f"Fingerprint mismatch: {stored_fingerprint} vs {current_fingerprint}"
            )

        # 4. Evaluate trial policy
        now = datetime.now(timezone.utc)
        status = self._policy.evaluate(now)
        if status == TrialStatus.EXPIRED:
            raise LicenseExpiredError("Trial period expired")
        elif status == TrialStatus.TAMPERED:
            raise IntegrityError("Time rollback detected")
