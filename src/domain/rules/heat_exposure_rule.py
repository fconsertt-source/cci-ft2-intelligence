# src/domain/rules/heat_exposure_rule.py
from typing import Any, Dict, Optional
from .base_rule import BaseRule


class HeatExposureRule(BaseRule):
    """Rule for evaluating heat exposure violations."""

    def evaluate(self, context: Any, stats: Dict[str, Any]) -> Optional[str]:
        # Check for critical heat (e.g., above 34°C for more than 2 hours)
        if stats.get("has_critical_heat", False):
            context.decision_reasons.append(
                f"حرارة حرجة: تجاوز 34°C لأكثر من ساعتين"
            )
            return "REJECTED_HEAT_C"

        # Check for CCM violation (heat duration above threshold)
        if stats.get("has_ccm_violation", False):
            context.decision_reasons.append(
                f"تجاوز الحد التراكمي (CCM): {stats.get('heat_duration', 0)} دقيقة"
            )
            return "REJECTED_HEAT_C"

        # Check max temperature against limits
        max_temp = stats.get("max_temp")
        if max_temp is not None:
            critical_limit = getattr(context, "critical_temp_limit", 10.0)
            if max_temp > critical_limit:
                context.decision_reasons.append(
                    f"حرارة حرجة: {max_temp:.1f}°C > {critical_limit}°C"
                )
                return "REJECTED_HEAT_C"

        context.decision_reasons.append("المقاييس الحرارية ضمن الحدود")
        return None