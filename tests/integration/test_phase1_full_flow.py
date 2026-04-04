import pytest
from unittest.mock import MagicMock
from src.application.services.center_impact_service import CenterImpactService
from src.application.dtos.validation_result import ValidationResult

class TestPhase1Logic:
    """اختبارات للمنطق الأساسي لـ Phase 1 — SSOT Verification"""

    def test_count_affected_centers_unique(self):
        """التأكد من أن العد يعتمد على المراكز الفريدة وليس السجلات"""
        def make_center(cid, has_data):
            c = MagicMock()
            c.id = cid
            unit = MagicMock()
            unit.ft2_entries = ["e1"] if has_data else []
            c.equipment_units = [unit]
            return c

        centers = [
            make_center("C1", True),
            make_center("C2", True),
            make_center("C3", False),
        ]

        count = CenterImpactService.count_affected_centers(centers)
        assert count == 2

    def test_ssot_verification_valid(self):
        """SSOT صحيح: 5 = 5"""
        is_valid, msg = CenterImpactService.verify_ssot(5, 5)
        assert is_valid is True
        assert "✅" in msg

    def test_ssot_verification_invalid(self):
        """SSOT مكسور: 5 ≠ 8 — الخلل الأصلي"""
        is_valid, msg = CenterImpactService.verify_ssot(5, 8)
        assert is_valid is False
        assert "❌" in msg
        assert "+3" in msg

    def test_validation_result_dto(self):
        """التأكد من أن ValidationResult يعمل"""
        result = ValidationResult(
            is_ssot_valid=True,
            yaml_count=5,
            affected_count=5,
            message="✅ OK"
        )
        assert result.is_ssot_valid is True
        assert result.yaml_count == 5
