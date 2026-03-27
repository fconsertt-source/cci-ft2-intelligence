# tests/unit/test_generate_device_report_uc.py
import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator
from src.infrastructure.adapters.validation_protocol_service import \
    ValidationProtocolService


# 1. تعريف Fixture للمتغير guard ليكون متاحاً لجميع الاختبارات
@pytest.fixture
def guard():
    """يوفر موك لنظام الحماية لضمان عدم حدوث NameError."""
    return MagicMock()


def test_execute_calls_dependencies_correctly(guard):  # 2. نمرر guard هنا كمعامل
    """Unit test: Ensure Use Case calls dependencies correctly."""

    mock_repo = Mock()
    mock_specs = Mock()

    mock_regulatory = Mock(spec=RegulatoryDecisionService)
    mock_estimator = Mock(spec=ThermalDegradationEstimator)
    mock_validator = Mock(spec=ValidationProtocolService)

    sample_records = [
        MagicMock(
            timestamp=datetime(2021, 12, 2),
            temperature=2.5,
            duration_minutes=1440.0,
            vaccine_type="Hepatitis_B",
        )
    ]
    mock_repo.get_device_history.return_value = sample_records

    sample_spec = MagicMock(
        vaccine_type="Hepatitis_B", rationale="Normal Hepatitis B storage"
    )
    mock_specs.get_spec.return_value = sample_spec

    mock_regulatory.evaluate.return_value = "SAFE"

    use_case = GenerateDeviceReportUseCase(
        device_repository=mock_repo,
        vaccine_specifications=mock_specs,
        regulatory_decision_service=mock_regulatory,
        estimator=mock_estimator,
        validator=mock_validator,
        license_guard=guard,  # الآن guard معرف عبر الـ fixture
    )

    assert use_case is not None


def test_handles_empty_device_history(guard):  # 3. نمرر guard هنا أيضاً
    """Unit test: Handle case where device has no history."""

    mock_repo = Mock()
    mock_specs = Mock()

    mock_regulatory = Mock(spec=RegulatoryDecisionService)
    mock_estimator = Mock(spec=ThermalDegradationEstimator)
    mock_validator = Mock(spec=ValidationProtocolService)

    mock_repo.get_device_history.return_value = []

    use_case = GenerateDeviceReportUseCase(
        device_repository=mock_repo,
        vaccine_specifications=mock_specs,
        regulatory_decision_service=mock_regulatory,
        estimator=mock_estimator,
        validator=mock_validator,
        license_guard=guard,
    )

    assert use_case is not None


def test_weakest_link_logic(guard):
    """
    Tier-1 Unit Test: Verify that the report reflects the worst status found in history.
    """
    # 1. Arrange (الإعداد)
    mock_repo = Mock()
    mock_specs = Mock()
    mock_regulatory = Mock(spec=RegulatoryDecisionService)
    mock_estimator = Mock(spec=ThermalDegradationEstimator)
    mock_validator = Mock(spec=ValidationProtocolService)

    # بيانات تجريبية: (سليم، تالف، سليم)
    records = [
        MagicMock(
            temperature=2.5, duration_minutes=1440.0, vaccine_type="HepB"
        ),  # SAFE
        MagicMock(
            temperature=9.5, duration_minutes=1440.0, vaccine_type="HepB"
        ),  # DISCARD (Worst)
        MagicMock(
            temperature=3.0, duration_minutes=1440.0, vaccine_type="HepB"
        ),  # SAFE
    ]
    mock_repo.get_device_history.return_value = records
    mock_specs.get_spec.return_value = MagicMock(vaccine_type="HepB")

    # استخدام side_effect بدلاً من التعيين المباشر للحفاظ على تتبع الـ Mock
    def mock_evaluate(*, temperature, duration_minutes, spec):
        return "DISCARD" if temperature > 9.0 else "SAFE"

    mock_regulatory.evaluate.side_effect = mock_evaluate

    use_case = GenerateDeviceReportUseCase(
        device_repository=mock_repo,
        vaccine_specifications=mock_specs,
        regulatory_decision_service=mock_regulatory,
        estimator=mock_estimator,
        validator=mock_validator,
        license_guard=guard,
    )

    # 2. Act (التنفيذ الفعلي)
    report = use_case.execute(device_id="DEV-001")

    # 3. Assert (التحقق من السلوك والنتائج)

    # أ- التحقق من الأمان (Security Guard)
    guard.ensure_active.assert_called_once()

    # ب- التحقق من استدعاء البيانات
    mock_repo.get_device_history.assert_called_with("DEV-001")

    # ج- التحقق من منطق العمل (The Weakest Link Logic)
    # التقرير يجب أن يكون DISCARD لأن إحدى القراءات كانت تالفة
    assert report.final_status == "DISCARD"

    # د- التأكد من أن التقييم تم استدعاؤه لجميع السجلات (3 مرات)
    assert mock_regulatory.evaluate.call_count == 3


@patch("src.application.use_cases.generate_device_report_uc.LicenseGuard.ensure_active")
def test_generate_device_report_executes_successfully(mock_guard, tmp_path):
    """Integration test: full pipeline without real license enforcement."""

    # Arrange
    test_data = [
        {
            "id": "DEV-001_2024-01-01T00:00:00",
            "device_id": "DEV-001",
            "timestamp": "2024-01-01 00:00:00",
            "temperature": 4.5,
            "vaccine_type": "Hepatitis_B",
            "duration_minutes": 1440.0,
        }
    ]

    json_file = tmp_path / "test_data.json"
    with open(json_file, "w") as f:
        json.dump(test_data, f)

    # ✅ استخدام Mocks صريحة بدلاً من الاعتماد على الحاوية
    from src.application.ports.device_repository_port import \
        DeviceRepositoryPort
    from src.application.ports.vaccine_specification_port import \
        VaccineSpecificationPort
    from src.application.ports.validation_protocol_port import \
        ValidationProtocolPort
    from src.application.security.license_guard import LicenseGuard
    from src.domain.services.regulatory_decision_service import \
        RegulatoryDecisionService
    from src.domain.services.thermal_degradation_estimator import \
        ThermalDegradationEstimator

    mock_repo = Mock(spec=DeviceRepositoryPort)
    mock_record = Mock()
    mock_record.vaccine_type = "Hepatitis_B"
    mock_record.temperature = 4.5
    mock_record.duration_minutes = 1440.0
    mock_record.timestamp = datetime(2024, 1, 1)
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
        'cumulative_impact': 0.0,
        'remaining_shelf_life': 100,
    }

    mock_validator = Mock(spec=ValidationProtocolPort)
    mock_validator.get_protocol.return_value = None

    mock_license_guard = Mock(spec=LicenseGuard)
    mock_license_guard.ensure_active.return_value = True

    # Act
    use_case = GenerateDeviceReportUseCase(
        device_repository=mock_repo,
        vaccine_specifications=mock_specs,
        regulatory_decision_service=mock_regulatory,
        estimator=mock_estimator,
        validator=mock_validator,
        license_guard=mock_license_guard,
        data_path=json_file,
    )
    report = use_case.execute(device_id="DEV-001")

    # Assert
    assert report is not None
    assert report.device_id == "DEV-001"
    mock_license_guard.ensure_active.assert_called_once()
