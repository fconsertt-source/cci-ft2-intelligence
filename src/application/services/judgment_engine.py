# src/application/services/judgment_engine.py
from typing import Any, Dict, List
from src.domain.rules.base_rule import BaseRule
from src.domain.rules.vvm_stage_rule import VVMStageRule
from src.domain.rules.heat_exposure_rule import HeatExposureRule


class JudgmentEngine:
    """Engine to orchestrate domain rules for decision making."""

    def __init__(self):
        self.rules: List[BaseRule] = [
            VVMStageRule(),
            HeatExposureRule(),
            # Add more rules as needed
        ]

    def judge(self, context: Any, stats: Dict[str, Any]) -> str:
        """
        Apply all rules to determine the final decision.

        Args:
            context: Domain context with decision_reasons list.
            stats: Analysis stats.

        Returns:
            Final decision string.
        """
        for rule in self.rules:
            decision = rule.safe_evaluate(context, stats)
            if decision:
                return decision
        return "ACCEPTED"