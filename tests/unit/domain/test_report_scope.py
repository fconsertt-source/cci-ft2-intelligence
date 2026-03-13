# tests/unit/domain/test_report_scope.py
"""Tests for ReportScope and ReportType enums."""

from src.domain.enums.report_scope import ReportScope, ReportType


def test_report_scope_members():
    assert ReportScope.DEVICE.value == "device"
    assert ReportScope.CENTER in ReportScope


def test_report_type_members():
    assert ReportType.OFFICIAL.value == "official"
    assert "arabic" in [t.value for t in ReportType]
