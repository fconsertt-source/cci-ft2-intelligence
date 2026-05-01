# tests/unit/domain/rules/test_vvm_stage_rule.py
import pytest
from unittest.mock import Mock
from src.domain.rules.vvm_stage_rule import VVMStageRule
from src.domain.enums.vvm_stage import VVMStage


class TestVVMStageRule:
    """Unit tests for VVMStageRule."""

    @pytest.fixture
    def rule(self):
        return VVMStageRule()

    @pytest.fixture
    def mock_context(self):
        context = Mock()
        context.decision_reasons = []
        return context

    @pytest.mark.parametrize("her,expected_stage,expected_decision", [
        (1.5, VVMStage.D, "REJECTED_HEAT_C"),
        (0.8, VVMStage.C, None),
        (0.5, VVMStage.B, None),
        (0.2, VVMStage.A, None),
        (0.05, VVMStage.NONE, None),
    ])
    def test_stage_evaluation(self, rule, mock_context, her, expected_stage, expected_decision):
        stats = {"her_ratio": her}
        result = rule.evaluate(mock_context, stats)

        assert mock_context.vvm_stage == expected_stage
        assert result == expected_decision
        if expected_decision:
            assert any("VVM" in reason for reason in mock_context.decision_reasons)

    def test_legacy_her_key(self, rule, mock_context):
        stats = {"her": 0.8}
        result = rule.evaluate(mock_context, stats)

        assert mock_context.vvm_stage == VVMStage.C
        assert result is None