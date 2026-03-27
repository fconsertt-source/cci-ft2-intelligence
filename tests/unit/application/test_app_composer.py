# tests/unit/application/test_app_composer.py
from src.application.app_composer import AppComposer
from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase


def test_composer_builds_uc():
    """
    Tests that the AppComposer can successfully build the GenerateDeviceReportUseCase.
    This test ensures the basic wiring of the composer is correct.
    """
    # Action
    uc = AppComposer.create_generate_device_report_uc()

    # Assert
    assert uc is not None
    assert isinstance(uc, GenerateDeviceReportUseCase)
