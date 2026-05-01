from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

# Assuming these classes exist from previous steps, based on di_container.py
from src.infrastructure.security.license_guard import LicenseGuard
from src.application.security.license_validator import LicenseValidator
from src.domain.policies.trial_policy import TrialPolicy
from src.infrastructure.security.encrypted_license_repository import \
    EncryptedLicenseRepository
from src.infrastructure.security.fingerprint_provider import \
    SystemFingerprintProvider

# This test file is specifically for the fingerprint tolerance logic,
# as requested. Testing a private method is not standard practice but can be
# done if the logic is complex and critical.


@pytest.fixture
def guard_instance():
    """
    Provides a LicenseGuard instance with mocked dependencies for testing
    isolated methods.
    """
    mock_license_repo = Mock(spec=EncryptedLicenseRepository)
    mock_validator = Mock(spec=LicenseValidator)
    mock_fingerprint_provider = Mock(spec=SystemFingerprintProvider)

    # The policy object is needed for the constructor
    policy = TrialPolicy(
        installation_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
        trial_duration_days=30,
        last_valid_run_time=None,
    )

    # Public key is also required
    public_key_pem = b"fake-public-key-for-testing"

    guard = LicenseGuard(
        license_repo=mock_license_repo,
        validator=mock_validator,
        policy=policy,
        fingerprint_provider=mock_fingerprint_provider,
        public_key_pem=public_key_pem,
    )
    return guard


def test_one_fingerprint_change_allowed(guard_instance):
    """
    Tests the tolerance logic: ONE component of the fingerprint can change.
    Example: machine_id changes, but os_uuid and timestamp remain the same.
    This test assumes the private method _fingerprint_tolerance_check exists
    and compares two pipe-delimited strings.
    """
    # Arrange
    # The user's request implies the following logic:
    # A fingerprint string is 'machine_id|os_uuid|install_timestamp'
    # The tolerance check allows for exactly ONE of these to differ.

    # Stored fingerprint from the license
    stored_fingerprint = "machine_id_A|os_uuid_XYZ|1672531200"

    # Current fingerprint from the system, with one part changed
    current_fingerprint = "machine_id_B|os_uuid_XYZ|1672531200"

    # Act & Assert
    # We are calling a private method, as per the user's request.
    assert (
        guard_instance._fingerprint_tolerance_check(
            stored_fingerprint, current_fingerprint
        )
        is True
    )


def test_two_fingerprint_changes_disallowed(guard_instance):
    """
    Tests that if MORE THAN ONE component changes, the check fails.
    """
    # Arrange
    stored_fingerprint = "machine_id_A|os_uuid_XYZ|1672531200"

    # Current fingerprint with two parts changed
    current_fingerprint = "machine_id_B|os_uuid_ABC|1672531200"

    # Act & Assert
    assert (
        guard_instance._fingerprint_tolerance_check(
            stored_fingerprint, current_fingerprint
        )
        is False
    )


def test_no_fingerprint_changes_is_allowed(guard_instance):
    """
    Tests that identical fingerprints pass the check.
    """
    # Arrange
    stored_fingerprint = "machine_id_A|os_uuid_XYZ|1672531200"
    current_fingerprint = "machine_id_A|os_uuid_XYZ|1672531200"

    # Act & Assert
    assert (
        guard_instance._fingerprint_tolerance_check(
            stored_fingerprint, current_fingerprint
        )
        is True
    )


def test_fingerprint_with_different_component_counts_fails(guard_instance):
    """
    Tests that malformed fingerprints fail the check.
    """
    # Arrange
    stored_fingerprint = "machine_id_A|os_uuid_XYZ|1672531200"
    current_fingerprint = "machine_id_A|os_uuid_XYZ"  # Missing a component

    # Act & Assert
    assert (
        guard_instance._fingerprint_tolerance_check(
            stored_fingerprint, current_fingerprint
        )
        is False
    )
