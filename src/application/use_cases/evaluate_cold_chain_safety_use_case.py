# src/application/use_cases/evaluate_cold_chain_safety_use_case.py
from itertools import tee
from typing import List

from src.domain.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, EvaluateColdChainSafetyResponse)
from src.domain.services.rules_engine import (apply_rules,
                                              calculate_center_stats)
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.services.exposure_analysis_service import ExposureAnalysisService
from src.domain.services.judgment_engine import JudgmentEngine
from src.domain.enums.vaccine_decision import VaccineDecision
from src.shared.config import get_config


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class DomainCenterContext:
    def __init__(
        self, request: EvaluateColdChainSafetyRequest, entries: List[TemperatureEntry]
    ):
        self.id = request.center_id
        self.name = request.center_name
        self.temperature_ranges = request.temperature_ranges or {"min": 2.0, "max": 8.0}
        self.decision_thresholds = request.decision_thresholds or {}
        self.ft2_entries = entries

        # Output fields expected by apply_rules
        self.decision = "UNKNOWN"
        self.vvm_stage = "NONE"
        self.alert_level = None
        self.stability_budget_consumed_pct = 0.0
        self.thaw_remaining_hours = None
        self.category_display = None
        self.decision_reasons = []

    @classmethod
    def from_request(cls, request: EvaluateColdChainSafetyRequest):
        entries = []
        # Ensure readings are sorted by timestamp
        sorted_readings = sorted(request.readings, key=lambda r: r.timestamp)

        for prev, curr in pairwise(sorted_readings):
            duration = (curr.timestamp - prev.timestamp).total_seconds() / 60.0
            entries.append(
                TemperatureEntry(
                    temperature=prev.value,
                    timestamp=prev.timestamp,
                    duration_minutes=duration,
                    device_id=prev.device_id,
                )
            )
        return cls(request, entries)


class EvaluateColdChainSafetyUseCase:
    """
    Pure Data Processing Engine.
    """

    def execute(
        self, request: EvaluateColdChainSafetyRequest
    ) -> EvaluateColdChainSafetyResponse:
        config = get_config()
        enable_supply_date = config.get_feature('CCI_ENABLE_SUPPLY_DATE')
        enable_heat_duration = config.get_feature('CCI_ENABLE_HEAT_DURATION')

        ctx = DomainCenterContext.from_request(request)

        if ctx.ft2_entries:
            # 1. Extract supply_date from vaccine_inventory if present
            supply_date = None
            if request.vaccine_inventory:
                supply_date = request.vaccine_inventory.get('supply_date')
                if not enable_supply_date:
                    supply_date = None  # feature disabled

            # 2. Calculate HER, CCM, etc.
            analysis_service = ExposureAnalysisService()
            analysis_results = analysis_service.analyze(
                readings=ctx.ft2_entries,
                spec=request.vaccine_spec,
                supply_date=supply_date,
                enable_supply_date=enable_supply_date,
            )

            # 3. Decision mapping for JudgmentEngine
            decision_map = {
                "DISCARD": VaccineDecision.DISCARD,
                "PARTIAL": VaccineDecision.PARTIAL,
                "SAFE": VaccineDecision.SAFE,
                "ACCEPTED": VaccineDecision.SAFE,
                "REJECTED_HEAT_C": VaccineDecision.DISCARD,
            }
            decision_enum = decision_map.get(ctx.decision, VaccineDecision.SAFE)

            # 4. Create judgment
            judgment_engine = JudgmentEngine()
            judgment = judgment_engine.judge(
                decision=decision_enum,
                decision_reason=" | ".join(ctx.decision_reasons),
                her_ratio=analysis_results.get("her_ratio", 0.0),
                ccm_index=analysis_results.get("ccm_index", "0"),
                freeze_detected=analysis_results.get("has_freeze", False),
                has_critical_heat=analysis_results.get("has_critical_heat", False),
            )

            # 5. Prepare extra_stats for rules engine (includes judgment data)
            extra_stats = {
                'her': analysis_results.get('her_ratio', 0.0),
                'ccm_index': analysis_results.get('ccm_index', '0'),
                'has_freeze': analysis_results.get('has_freeze', False),
                'has_critical_heat': analysis_results.get('has_critical_heat', False),
                'judgment_risk': judgment.risk_level,
                'judgment_icon': judgment.risk_icon,
                'confidence': judgment.confidence,
                'requires_review': judgment.requires_human_review,
                'her_percentage': judgment.her_percentage,
                'judgment_narrative': judgment.narrative,
            }

            # 6. Apply rules with feature flag and extra stats
            apply_rules(ctx, extra_stats=extra_stats, enable_heat_duration=enable_heat_duration)

            # 7. Calculate basic stats (for legacy compatibility)
            stats = calculate_center_stats(ctx)
            # Merge extra_stats into stats (so they are available in response)
            stats.update(extra_stats)
        else:
            ctx.decision = "NO_DATA"
            stats = {"has_freeze": False, "has_ccm_violation": False}

        return EvaluateColdChainSafetyResponse.from_context(ctx, stats)