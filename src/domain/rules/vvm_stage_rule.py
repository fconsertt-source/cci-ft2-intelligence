# src/domain/rules/vvm_stage_rule.py
from typing import Any, Dict, Optional
from src.domain.enums.vvm_stage import VVMStage
from .base_rule import BaseRule


class VVMStageRule(BaseRule):
    """Rule for determining VVM stage based on HER ratio."""

    def evaluate(self, context: Any, stats: Dict[str, Any]) -> Optional[str]:
        # Support both her_ratio (from ExposureAnalysisService) and her (legacy)
        her = stats.get("her_ratio", stats.get("her", 0.0))

        if her >= 1.0:
            context.vvm_stage = VVMStage.D
            context.decision_reasons.append(
                f"VVM المرحلة D: HER ratio = {her:.3f} ≥ 1.0 → منتهي حرارياً"
            )
            return "REJECTED_HEAT_C"
        elif her >= 0.7:
            context.vvm_stage = VVMStage.C
            context.decision_reasons.append(f"VVM المرحلة C: HER = {her:.3f}")
        elif her >= 0.4:
            context.vvm_stage = VVMStage.B
            context.decision_reasons.append(f"VVM المرحلة B: HER = {her:.3f}")
        elif her >= 0.1:
            context.vvm_stage = VVMStage.A
            context.decision_reasons.append(f"VVM المرحلة A: HER = {her:.3f}")
        else:
            context.vvm_stage = VVMStage.NONE

        return None