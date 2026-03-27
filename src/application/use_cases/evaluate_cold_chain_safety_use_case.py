# src/application/use_cases/evaluate_cold_chain_safety_use_case.py
from itertools import tee
from typing import List

from src.domain.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, EvaluateColdChainSafetyResponse)
from src.domain.services.rules_engine import (apply_rules,
                                              calculate_center_stats)
from src.domain.value_objects.temperature_entry import TemperatureEntry


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
        ctx = DomainCenterContext.from_request(request)

        if ctx.ft2_entries:
            apply_rules(ctx)
            stats = calculate_center_stats(ctx)
        else:
            ctx.decision = "NO_DATA"
            stats = {"has_freeze": False, "has_ccm_violation": False}

        return EvaluateColdChainSafetyResponse.from_context(ctx, stats)
