# tests/conftest.py

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from src.application.services.vaccines_report_generator import \
    VaccinesReportGenerator
from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase
# B4 imports
from src.domain.entities.equipment_vaccine import EquipmentVaccine
from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.enums.vvm_stage import VVMStage
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator
from src.domain.services.vaccine_assessment_service import \
    VaccineAssessmentService
from src.infrastructure.adapters.json_device_repository import \
    JsonDeviceRepository
from src.infrastructure.adapters.json_vaccine_spec_repository import \
    JsonVaccineSpecRepository
from src.infrastructure.adapters.validation_protocol_service import \
    ValidationProtocolService

# ------------------------------------------------------------------
# Test Double
# ------------------------------------------------------------------


class DummyLicenseGuard:
    """Test double that always allows execution."""

    def ensure_active(self) -> None:
        return None


# ------------------------------------------------------------------
# General Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def sample_json_data():
    """Normal temperature data."""
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
    """Temperature excursion data."""
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

    json_file = tmp_path / "test_data.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sample_json_data, f, ensure_ascii=False)

    device_repo = JsonDeviceRepository(json_path=json_file)
    vaccine_spec_port = JsonVaccineSpecRepository()
    regulatory_decision = RegulatoryDecisionService()
    estimator = ThermalDegradationEstimator()
    validator = ValidationProtocolService()

    return GenerateDeviceReportUseCase(
        device_repository=device_repo,
        vaccine_specifications=vaccine_spec_port,
        regulatory_decision_service=regulatory_decision,
        estimator=estimator,
        validator=validator,
        license_guard=DummyLicenseGuard(),
    )


# ------------------------------------------------------------------
# B4 Vaccine Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def fixed_today():
    """Fixed date to avoid expiry variability."""
    return date(2024, 6, 15)


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent.parent / "data" / "test_data"


@pytest.fixture
def equipment_vaccines(test_data_dir):

    json_path = test_data_dir / "equipment_vaccines_test.json"

    if not json_path.exists():
        pytest.skip("Test data file not found")

    with open(json_path) as f:
        data = json.load(f)

    vvm_map = {
        1: VVMStage.NONE,
        2: VVMStage.A,
        3: VVMStage.B,
        4: VVMStage.C,
        5: VVMStage.D,
    }

    vaccines = []

    for item in data:

        vvm_stage = None

        if item.get("has_vvm"):
            vvm_stage = vvm_map.get(item.get("vvm_stage"))

        vaccine = EquipmentVaccine(
            center_id=item.get("center_id", "CENTER_001"),
            equipment_id=item["equipment_id"],
            entry_id=item["entry_id"],
            vaccine_type=item["vaccine_type"],
            batch_number=item["batch_number"],
            expiry_date=datetime.strptime(item["expiry_date"], "%Y-%m-%d").date(),
            vvm_stage=vvm_stage,
            has_vvm=item.get("has_vvm", False),
        )

        vaccines.append(vaccine)

    return vaccines


# ------------------------------------------------------------------
# Temperature Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def temperature_readings():

    base = datetime(2024, 6, 1, 10, 0)

    return {
        "EQ001": [
            TemperatureReading("test", 5.0, base, duration_hours=1.0),
            TemperatureReading("test", 5.2, base.replace(hour=11), duration_hours=1.0),
        ],
        "EQ002": [
            TemperatureReading("test", 35.0, base, duration_hours=1.0),
            TemperatureReading("test", 36.0, base.replace(hour=11), duration_hours=1.0),
            TemperatureReading("test", 35.5, base.replace(hour=12), duration_hours=1.0),
        ],
    }


@pytest.fixture
def freezer_temperature_readings():

    base = datetime(2024, 6, 1, 10, 0)

    return {
        "EQ004": [
            TemperatureReading("test", -2.0, base, duration_hours=1.0),
            TemperatureReading("test", -1.5, base.replace(hour=11), duration_hours=1.0),
        ]
    }


@pytest.fixture
def high_her_temperature_readings():
    """قراءات حرارية تؤدي إلى HER = 0.092855 (محسوب بدقة)."""
    base_time = datetime(2024, 6, 1, 10, 0)

    return {
        "EQ003": [
            TemperatureReading(
                vaccine_id="test",
                value=33.0,
                recorded_at=base_time,
                duration_hours=72.0,
            ),
        ],
    }


@pytest.fixture
def partial_temperature_readings():
    """قراءات حرارية تؤدي إلى HER = 0.035556 (محسوب بدقة)."""
    base_time = datetime(2024, 6, 1, 10, 0)

    return {
        "EQ005": [
            TemperatureReading(
                vaccine_id="test",
                value=25.0,
                recorded_at=base_time,
                duration_hours=48.0,
            ),
        ],
    }


@pytest.fixture
def excursion_use_case(tmp_path, excursion_json_data):

    json_file = tmp_path / "excursion_test.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(excursion_json_data, f, ensure_ascii=False)

    device_repo = JsonDeviceRepository(json_path=json_file)

    return GenerateDeviceReportUseCase(
        device_repository=device_repo,
        vaccine_specifications=JsonVaccineSpecRepository(),
        regulatory_decision_service=RegulatoryDecisionService(),
        estimator=ThermalDegradationEstimator(),
        validator=ValidationProtocolService(),
        license_guard=DummyLicenseGuard(),
    )


# ------------------------------------------------------------------
# Services
# ------------------------------------------------------------------


@pytest.fixture
def vaccine_assessment_service():
    return VaccineAssessmentService()


@pytest.fixture
def report_generator():
    return VaccinesReportGenerator()


# ------------------------------------------------------------------
# Pytest markers
# ------------------------------------------------------------------


def pytest_configure(config):

    config.addinivalue_line("markers", "unit")
    config.addinivalue_line("markers", "integration")
    config.addinivalue_line("markers", "architecture")
    config.addinivalue_line("markers", "b4")
