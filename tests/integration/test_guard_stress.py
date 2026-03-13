#!/usr/bin/env python3
"""اختبار إجهاد لـ LicenseGuard مع GenerateDeviceReportUseCase"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_guard():
    """Mock لـ LicenseGuard مع spec للصراحة النوعية"""
    from src.application.security.license_guard import LicenseGuard

    guard = Mock(spec=LicenseGuard)
    guard.ensure_active.return_value = True
    return guard


@pytest.fixture
def mock_dependencies():
    """Mocks صريحة لجميع Dependencies الـ 6"""
    from src.application.ports.device_repository_port import DeviceRepositoryPort
    from src.application.ports.vaccine_specification_port import (
        VaccineSpecificationPort,
    )
    from src.application.ports.validation_protocol_port import ValidationProtocolPort
    from src.domain.services.regulatory_decision_service import (
        RegulatoryDecisionService,
    )
    from src.domain.services.thermal_degradation_estimator import (
        ThermalDegradationEstimator,
    )

    mock_repo = Mock(spec=DeviceRepositoryPort)
    mock_record = Mock()
    mock_record.vaccine_type = "Hepatitis_B"
    mock_repo.get_device_history.return_value = [mock_record]

    mock_spec = Mock()
    mock_spec.vaccine_type = "Hepatitis_B"
    mock_spec.rationale = "Test rationale"

    mock_specs = Mock(spec=VaccineSpecificationPort)
    mock_specs.get_spec.return_value = mock_spec

    mock_regulatory = Mock(spec=RegulatoryDecisionService)
    mock_regulatory.evaluate.return_value = "SAFE"

    mock_estimator = Mock(spec=ThermalDegradationEstimator)
    mock_estimator.calculate_cumulative_impact.return_value = {
        "cumulative_impact": 0.0,
        "remaining_shelf_life": 100,
    }

    mock_validator = Mock(spec=ValidationProtocolPort)
    mock_validator.get_protocol.return_value = None

    return {
        "device_repository": mock_repo,
        "vaccine_specifications": mock_specs,
        "regulatory_decision_service": mock_regulatory,
        "estimator": mock_estimator,
        "validator": mock_validator,
    }


def test_repeated_execution_calls_guard_repeatedly(mock_dependencies, mock_guard):
    """
    التحقق من أن LicenseGuard يُستدعى مع كل تنفيذ.

    ✅ يستخدم Dependency Injection الصحيح
    ✅ لا يعتمد على container
    ✅ معزول وسريع
    """
    from src.application.use_cases.generate_device_report_uc import (
        GenerateDeviceReportUseCase,
    )

    uc = GenerateDeviceReportUseCase(
        device_repository=mock_dependencies["device_repository"],
        vaccine_specifications=mock_dependencies["vaccine_specifications"],
        regulatory_decision_service=mock_dependencies["regulatory_decision_service"],
        estimator=mock_dependencies["estimator"],
        validator=mock_dependencies["validator"],
        license_guard=mock_guard,
        data_path=None,
    )

    for i in range(100):
        from src.application.use_cases.requests import GenerateDeviceReportRequest

        req = GenerateDeviceReportRequest(device_id="DEV-001")
        uc.execute(req)

    assert (
        mock_guard.ensure_active.call_count == 100
    ), f"Expected 100 calls, got {mock_guard.ensure_active.call_count}"
