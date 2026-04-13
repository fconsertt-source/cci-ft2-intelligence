# tests/bdd/conftest.py
from unittest.mock import MagicMock, Mock
from datetime import datetime, timezone
import pytest

from src.application.use_cases.generate_device_report_uc import GenerateDeviceReportUseCase
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import ThermalDegradationEstimator
from src.infrastructure.adapters.validation_protocol_service import ValidationProtocolService


def _build_use_case(records, regulatory_side_effect=None):
    guard = MagicMock()
    mock_repo = Mock()
    mock_specs = Mock()
    mock_regulatory = Mock(spec=RegulatoryDecisionService)
    mock_estimator = Mock(spec=ThermalDegradationEstimator)
    mock_validator = Mock(spec=ValidationProtocolService)

    mock_repo.get_device_history.return_value = records

    sample_spec = MagicMock(
        vaccine_type="Hepatitis_B",
        rationale="Standard Hepatitis B cold chain protocol",
    )
    mock_specs.get_spec.return_value = sample_spec

    if regulatory_side_effect:
        mock_regulatory.evaluate.side_effect = regulatory_side_effect
    else:
        mock_regulatory.evaluate.return_value = "SAFE"

    mock_estimator.calculate_cumulative_impact.return_value = {
        "remaining_shelf_life": 80.0,
        "cumulative_vvm_impact": 0.1,
        "degradation_score": 0.05,
    }

    return GenerateDeviceReportUseCase(
        device_repository=mock_repo,
        vaccine_specifications=mock_specs,
        regulatory_decision_service=mock_regulatory,
        estimator=mock_estimator,
        validator=mock_validator,
        license_guard=guard,
    )


@pytest.fixture
def device_use_case():
    records = [
        MagicMock(
            device_id="130600112764",
            timestamp=datetime(2021, 12, 1, tzinfo=timezone.utc),
            temperature=4.0,
            duration_minutes=1440.0,
            vaccine_type="Hepatitis_B",
        ),
        MagicMock(
            device_id="130600112764",
            timestamp=datetime(2021, 12, 2, tzinfo=timezone.utc),
            temperature=5.0,
            duration_minutes=1440.0,
            vaccine_type="Hepatitis_B",
        ),
    ]
    return _build_use_case(records)


@pytest.fixture
def excursion_use_case():
    def regulatory_side_effect(temperature, duration_minutes, spec):
        return "PARTIAL" if temperature > 8.0 else "SAFE"

    records = [
        MagicMock(
            device_id="130600112764",
            timestamp=datetime(2021, 12, 1, tzinfo=timezone.utc),
            temperature=4.0,
            duration_minutes=1440.0,
            vaccine_type="Hepatitis_B",
        ),
        MagicMock(
            device_id="130600112764",
            timestamp=datetime(2021, 12, 2, tzinfo=timezone.utc),
            temperature=9.0,
            duration_minutes=1440.0,
            vaccine_type="Hepatitis_B",
        ),
    ]
    return _build_use_case(records, regulatory_side_effect=regulatory_side_effect)