# tests/conftest.py
import json
from datetime import datetime

import pytest

from src.application.use_cases.generate_device_report_uc import (
    GenerateDeviceReportUseCase,
)
from src.domain.calculators.q10_thermal_calculator import Q10ThermalCalculator
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import (
    ThermalDegradationEstimator,
)
from src.infrastructure.adapters.json_device_repository import JsonDeviceRepository
from src.infrastructure.adapters.json_vaccine_spec_repository import (
    JsonVaccineSpecRepository,
)
from src.infrastructure.adapters.validation_protocol_service import (
    ValidationProtocolService,
)


# ------------------------------------------------------------------
# Test Doubles (يجب تعريفها قبل الاستخدام)
# ------------------------------------------------------------------
class DummyLicenseGuard:
    """Test double that always allows execution."""

    def ensure_active(self) -> None:
        return None


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------
@pytest.fixture
def sample_json_data():
    """Sample data for normal temperature scenario."""
    return [
        {
            "id": "130600112764_2021-12-01T00:00:00",
            "device_id": "130600112764",
            "timestamp": "2021-12-01 00:00:00",
            "temperature": 3.0,
            "duration_minutes": 1440.0,
            "vaccine_type": "Hepatitis_B",
        },
        {
            "id": "130600112764_2021-12-02T00:00:00",
            "device_id": "130600112764",
            "timestamp": "2021-12-02 00:00:00",
            "temperature": 4.0,
            "duration_minutes": 1440.0,
            "vaccine_type": "Hepatitis_B",
        },
    ]


@pytest.fixture
def excursion_json_data():
    """Sample data for temperature excursion scenario."""
    return [
        {
            "id": "130600112764_2021-12-01T00:00:00",
            "device_id": "130600112764",
            "timestamp": "2021-12-01 00:00:00",
            "temperature": 9.0,
            "duration_minutes": 1440.0,
            "vaccine_type": "Hepatitis_B",
        },
        {
            "id": "130600112764_2021-12-02T00:00:00",
            "device_id": "130600112764",
            "timestamp": "2021-12-02 00:00:00",
            "temperature": 2.5,
            "duration_minutes": 1440.0,
            "vaccine_type": "Hepatitis_B",
        },
    ]


@pytest.fixture
def device_use_case(tmp_path, sample_json_data):
    """Setup Use Case with temporary JSON file."""
    json_file = tmp_path / "test_data.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sample_json_data, f, ensure_ascii=False)

    device_repo = JsonDeviceRepository(json_path=json_file)
    vaccine_spec_port = JsonVaccineSpecRepository()
    regulatory_decision = RegulatoryDecisionService()
    estimator = ThermalDegradationEstimator()
    validator = ValidationProtocolService()
    license_guard = DummyLicenseGuard()

    return GenerateDeviceReportUseCase(
        device_repository=device_repo,
        vaccine_specifications=vaccine_spec_port,
        regulatory_decision_service=regulatory_decision,
        estimator=estimator,
        validator=validator,
        license_guard=license_guard,
    )


@pytest.fixture
def excursion_use_case(tmp_path, excursion_json_data):
    """Setup Use Case with excursion data."""
    json_file = tmp_path / "excursion_test.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(excursion_json_data, f, ensure_ascii=False)

    device_repo = JsonDeviceRepository(json_path=json_file)
    vaccine_spec_port = JsonVaccineSpecRepository()
    regulatory_decision = RegulatoryDecisionService()
    estimator = ThermalDegradationEstimator()
    validator = ValidationProtocolService()
    license_guard = DummyLicenseGuard()

    return GenerateDeviceReportUseCase(
        device_repository=device_repo,
        vaccine_specifications=vaccine_spec_port,
        regulatory_decision_service=regulatory_decision,
        estimator=estimator,
        validator=validator,
        license_guard=license_guard,
    )


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "architecture: architecture tests")
