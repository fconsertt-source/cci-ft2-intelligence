# src/application/use_cases/evaluate_cold_chain_safety_use_case.py
from itertools import tee
from typing import List

from src.domain.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, EvaluateColdChainSafetyResponse)
from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.services.rules_engine import apply_rules
from src.domain.value_objects.temperature_entry import TemperatureEntry


def pairwise(iterable):
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
        self.ft2_entries = entries  # Holds TemperatureEntry list

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
        # Check if incoming readings have duration (FT2 Split Strategy)
        has_duration = any(
            hasattr(r, "duration_minutes")
            and r.duration_minutes is not None
            and r.duration_minutes > 0
            for r in request.readings
        )

        if has_duration:
            # Pass through exactly (Raw Hist/Split Mode)
            for r in request.readings:
                entries.append(
                    TemperatureEntry(
                        temperature=r.value,
                        timestamp=r.timestamp,
                        duration_minutes=r.duration_minutes,
                        device_id=r.device_id,
                        # Pass metadata if possible via a backdoor or assume Usecase handles it
                        # For now, TemperatureEntry is a Value Object.
                        # Note: We rely on the request.readings matching TemperatureEntry structure
                    )
                )
                # Hack: Attach the batch/meta string to the entry if TemperatureEntry allows dynamic attributes
                # or if we map it.
                entries[-1].meta = getattr(r, "batch", None)
        else:
            # Legacy Pairwise calculation for raw loggers
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
    Orchestrates parsing, risk analysis, and response formulation.
    """

    def execute(
        self, request: EvaluateColdChainSafetyRequest
    ) -> EvaluateColdChainSafetyResponse:
        ctx = DomainCenterContext.from_request(request)

        if ctx.ft2_entries:
            # 1. Decision Logic (Rules Engine)
            apply_rules(ctx)

            # 2. Mathematical Exposure Analysis (HER/CCM)
            analysis_service = ExposureAnalysisService()
            stats = analysis_service.analyze(ctx.ft2_entries)

            # Merge logic decision with stats
            stats["decision"] = ctx.decision
            stats["decision_reasons"] = ctx.decision_reasons
        else:
            stats = {"has_freeze": False, "has_ccm_violation": False}

        # The response factory uses 'stats' to populate fields
        return EvaluateColdChainSafetyResponse.from_context(ctx, stats)
