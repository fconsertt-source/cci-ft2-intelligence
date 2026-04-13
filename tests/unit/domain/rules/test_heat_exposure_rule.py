# tests/unit/domain/rules/test_heat_exposure_rule.py
import pytest
from unittest.mock import Mock
from src.domain.rules.heat_exposure_rule import HeatExposureRule


class TestHeatExposureRule:
    """Unit tests for HeatExposureRule."""

    @pytest.fixture
    def rule(self):
        return HeatExposureRule()

    @pytest.fixture
    def mock_context(self):
        context = Mock()
        context.decision_reasons = []
        context.critical_temp_limit = 10.0
        return context

    def test_critical_heat_rejection(self, rule, mock_context):
        stats = {"has_critical_heat": True}
        result = rule.evaluate(mock_context, stats)

        assert result == "REJECTED_HEAT_C"
        assert any("حرارة حرجة" in reason for reason in mock_context.decision_reasons)

    def test_ccm_violation_rejection(self, rule, mock_context):
        stats = {"has_heat_duration_breach": True, "heat_duration": 120}
        result = rule.evaluate(mock_context, stats)

        assert result == "REJECTED_HEAT_C"
        assert any("CCM" in reason for reason in mock_context.decision_reasons)

    def test_max_temp_exceedance(self, rule, mock_context):
        stats = {"max_temp": 15.0}
        result = rule.evaluate(mock_context, stats)

        assert result == "REJECTED_HEAT_C"
        assert any("15.0°C" in reason for reason in mock_context.decision_reasons)

    def test_no_violation_acceptance(self, rule, mock_context):
        stats = {"max_temp": 5.0, "has_critical_heat": False, "has_heat_duration_breach": False, "has_heat_duration_breach": False}
        result = rule.evaluate(mock_context, stats)

        assert result is None
        assert any("ضمن الحدود" in reason for reason in mock_context.decision_reasons)