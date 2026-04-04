"""
اختبار التكامل الكامل للـ Lifecycle.
يُشغّل ManageFileLifecycleUseCase مع Mocks حقيقية.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.shared.utils.time_utils import utc_now_datetime

from src.application.use_cases.manage_file_lifecycle import (
    ManageFileLifecycleUseCase
)

class TestLifecycleFullFlow:

    @pytest.fixture
    def tmp_csv(self, tmp_path):
        """ملف CSV مؤقت بجهاز مسجل"""
        f = tmp_path / "130600112663_converted.csv"
        f.write_text("timestamp,temperature\n2024-01-01,4.5\n")
        return f

    @pytest.fixture
    def unknown_csv(self, tmp_path):
        """ملف CSV بجهاز غير مسجل"""
        f = tmp_path / "130600112999_unknown.csv"
        f.write_text("timestamp,temperature\n2024-01-01,4.5\n")
        return f

    @pytest.fixture
    def use_case(self):
        registry = MagicMock()
        registry.is_processed.return_value = False

        center_reg = MagicMock()
        center_reg.get_all_device_ids.return_value = frozenset([
            "130600112663", "130600112758", "130600113437",
            "130600113438", "130600205054"
        ])

        return ManageFileLifecycleUseCase(
            file_registry=registry,
            center_registry=center_reg
        )

    def test_registered_device_goes_to_ready(self, use_case, tmp_csv):
        result = use_case.classify_files([tmp_csv], run_id="test_01")
        assert tmp_csv in result.ready_for_processing
        assert len(result.quarantine) == 0

    def test_unregistered_device_goes_to_quarantine(self, use_case, unknown_csv):
        result = use_case.classify_files([unknown_csv], run_id="test_02")
        quarantined_paths = [p for p, _, _ in result.quarantine]
        assert unknown_csv in quarantined_paths
        assert len(result.ready_for_processing) == 0

    def test_already_processed_file_skipped(self, tmp_csv):
        registry = MagicMock()
        registry.is_processed.return_value = True  # سبق معالجته

        center_reg = MagicMock()
        center_reg.get_all_device_ids.return_value = frozenset(["130600112663"])

        use_case = ManageFileLifecycleUseCase(registry, center_reg)
        result = use_case.classify_files([tmp_csv], run_id="test_03")

        assert tmp_csv in result.already_processed
        assert len(result.ready_for_processing) == 0

    def test_ssot_violation_detected(self, use_case, unknown_csv):
        result = use_case.classify_files([unknown_csv], run_id="test_04")
        assert result.ssot_compliant is False

    def test_summary_bilingual(self, use_case, tmp_csv):
        result = use_case.classify_files([tmp_csv], run_id="test_05")
        assert "جاهزة" in result.summary_ar()
        assert "Ready" in result.summary_en()