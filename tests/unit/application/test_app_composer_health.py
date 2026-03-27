# tests/unit/application/test_app_composer_health.py
"""Verify AppComposer health check and new use case builders."""

from src.application.app_composer import AppComposer
from src.application.use_cases.import_ft2_bundle_uc import \
    ImportFT2BundleUseCase


def test_health_check_passes():
    assert AppComposer.health_check() is True


def test_can_build_import_uc():
    uc = AppComposer.create_import_ft2_bundle_uc()
    assert isinstance(uc, ImportFT2BundleUseCase)
