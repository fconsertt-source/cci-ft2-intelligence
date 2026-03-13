from unittest.mock import Mock, patch

import pytest

from src.application.ports.device_repository_port import DeviceRepositoryPort
from src.application.ports.vaccine_specification_port import VaccineSpecificationPort
from src.application.ports.validation_protocol_port import ValidationProtocolPort
from src.application.security.license_guard import LicenseGuard

# Assume these modules and classes exist from previous work
from src.application.use_cases.generate_device_report_uc import (
    GenerateDeviceReportUseCase,
)
from src.application.use_cases.requests import GenerateDeviceReportRequest
from src.domain.exceptions.license_exceptions import LicenseExpiredError
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import (
    ThermalDegradationEstimator,
)


@pytest.fixture
def mock_dependencies():
    """Provides a dictionary of mocked dependencies for the use case."""
    return {
        "device_repository": Mock(spec=DeviceRepositoryPort),
        "vaccine_specifications": Mock(spec=VaccineSpecificationPort),
        "regulatory_decision_service": Mock(spec=RegulatoryDecisionService),
        "estimator": Mock(spec=ThermalDegradationEstimator),
        "validator": Mock(spec=ValidationProtocolPort),
    }


def test_guard_blocks_expired_use_case(mock_dependencies):
    """
    Verifies that the use case is blocked if the license guard raises a LicenseExpiredError.
    """
    # 1. Arrange
    mock_guard = Mock(spec=LicenseGuard)
    mock_guard.ensure_active.side_effect = LicenseExpiredError("Trial has expired.")

    # Instantiate the use case with real and mock components
    uc = GenerateDeviceReportUseCase(
        **mock_dependencies,
        license_guard=mock_guard,
    )

    # 2. Act & Assert
    with pytest.raises(LicenseExpiredError, match="Trial has expired."):
        req = GenerateDeviceReportRequest(device_id="DEV-001")
        uc.execute(req)

    # 3. Verify
    mock_guard.ensure_active.assert_called_once()
    # Ensure no other methods were called on dependencies
    mock_dependencies["device_repository"].get_device_history.assert_not_called()


def test_use_case_proceeds_with_active_license(mock_dependencies):
    """
    Ensures the use case executes normally when the license is active.
    This is a simplified happy-path test to contrast with the guard block.
    """
    # 1. Arrange
    mock_guard = Mock(spec=LicenseGuard)
    mock_guard.ensure_active.return_value = None  # No exception

    # Mock the return values for the rest of the use case execution
    mock_repo = mock_dependencies["device_repository"]
    mock_spec_port = mock_dependencies["vaccine_specifications"]
    mock_regulatory_service = mock_dependencies["regulatory_decision_service"]

    # Need to mock the chain of calls inside execute()
    mock_records = [Mock(vaccine_type="MTR", temperature=4.0, duration_minutes=10)]
    mock_repo.get_device_history.return_value = mock_records

    mock_spec = Mock()
    mock_spec.vaccine_type = "MTR"
    mock_spec.rationale = "Test Rationale"
    mock_spec_port.get_spec.return_value = mock_spec
    mock_regulatory_service.evaluate.return_value = "SAFE"

    # Instantiate the use case
    uc = GenerateDeviceReportUseCase(
        **mock_dependencies,
        license_guard=mock_guard,
    )

    # 2. Act
    # We can ignore the result, we are just checking the flow
    req = GenerateDeviceReportRequest(device_id="DEV-001")
    uc.execute(req)

    # 3. Assert
    mock_guard.ensure_active.assert_called_once()
    mock_repo.get_device_history.assert_called_once_with("DEV-001")
    mock_spec_port.get_spec.assert_called_once_with("MTR")
