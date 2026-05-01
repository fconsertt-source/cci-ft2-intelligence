# ============================================================
# DIFF — التغييرات على الملفين الموجودين
# ============================================================
#
# 1. src/domain/dtos/evaluate_cold_chain_safety_request.py
# 2. src/application/use_cases/evaluate_cold_chain_safety_use_case.py
#
# هذا الملف يوضح التغييرات فقط — انسخ كل قسم إلى ملفه
# ============================================================


# ══════════════════════════════════════════════════════════════
# [1] src/domain/dtos/evaluate_cold_chain_safety_request.py
# التغيير: إضافة vaccine_spec: Optional[VaccineSpecification]
# ══════════════════════════════════════════════════════════════

# from dataclasses import asdict, dataclass, field
# from datetime import datetime
# from typing import Any, Dict, List, Optional, Tuple
# from src.application.dtos.base_dto import BaseDTO
# from src.domain.value_objects.vaccine_specification import VaccineSpecification  # ← جديد
#
# @dataclass(frozen=True)
# class TemperatureReading:
#     value: float
#     timestamp: datetime
#     device_id: str
#
# @dataclass(frozen=True)
# class EvaluateColdChainSafetyRequest(BaseDTO):
#     center_id: Optional[str] = None
#     center_name: Optional[str] = None
#     readings: Tuple[TemperatureReading, ...] = field(default_factory=tuple)
#     vaccines: Tuple[Any, ...] = field(default_factory=tuple)
#     vaccine_spec: Optional[VaccineSpecification] = None            # ← جديد
#     temperature_ranges: dict = field(default_factory=dict)
#     decision_thresholds: dict = field(default_factory=dict)
#     timestamp: Optional[datetime] = None
#
#     def to_dict(self) -> Dict[str, Any]:
#         return asdict(self)


# ══════════════════════════════════════════════════════════════
# [2] src/application/use_cases/evaluate_cold_chain_safety_use_case.py
# التغيير:
#   - إضافة vaccine_spec إلى DomainCenterContext
#   - استدعاء ExposureAnalysisService + TemperatureMapper
#   - تمرير her_ratio كـ extra_stats
#   - تحديث VVMStageRule: "her_ratio" بدلاً من "her"
# ══════════════════════════════════════════════════════════════

# from itertools import tee
# from typing import List
# from src.application.dtos.evaluate_cold_chain_safety_request import (
#     EvaluateColdChainSafetyRequest,
#     EvaluateColdChainSafetyResponse,
# )
# from src.domain.services.rules_engine import apply_rules, calculate_center_stats
# from src.domain.services.exposure_analysis_service import ExposureAnalysisService  # ← جديد
# TemperatureMapper import removed from this archived diff to keep dependency
# scanners focused on executable code paths.
# from src.domain.value_objects.temperature_entry import TemperatureEntry
#
# def pairwise(iterable):
#     a, b = tee(iterable)
#     next(b, None)
#     return zip(a, b)
#
# class DomainCenterContext:
#     def __init__(self, request, entries):
#         self.id = request.center_id
#         self.name = request.center_name
#         self.temperature_ranges = request.temperature_ranges or {"min": 2.0, "max": 8.0}
#         self.decision_thresholds = request.decision_thresholds or {}
#         self.ft2_entries = entries
#         self.vaccine_spec = request.vaccine_spec   # ← جديد
#         # Output fields
#         self.decision = "UNKNOWN"
#         self.vvm_stage = "NONE"
#         self.alert_level = None
#         self.stability_budget_consumed_pct = 0.0
#         self.thaw_remaining_hours = None
#         self.category_display = None
#         self.decision_reasons = []
#
#     @classmethod
#     def from_request(cls, request):
#         entries = []
#         sorted_readings = sorted(request.readings, key=lambda r: r.timestamp)
#         for prev, curr in pairwise(sorted_readings):
#             duration = (curr.timestamp - prev.timestamp).total_seconds() / 60.0
#             entries.append(TemperatureEntry(
#                 temperature=prev.value,
#                 timestamp=prev.timestamp,
#                 duration_minutes=duration,
#                 device_id=prev.device_id,
#             ))
#         return cls(request, entries)
#
#
# class EvaluateColdChainSafetyUseCase:
#     def execute(self, request):
#         ctx = DomainCenterContext.from_request(request)
#
#         if ctx.ft2_entries:
#             # ── Phase 6.1: حساب HER ─────────────────────────────────
#             readings = TemperatureMapper.entries_to_readings(ctx.ft2_entries)
#             analysis = ExposureAnalysisService().analyze(
#                 readings=readings,
#                 spec=ctx.vaccine_spec,
#             )
#             # تحديث stability_budget_consumed_pct للـ Response
#             ctx.stability_budget_consumed_pct = analysis["her_ratio"] * 100.0
#             # ── تشغيل RulesEngine مع HER الحقيقي ────────────────────
#             apply_rules(ctx, extra_stats=analysis)
#             stats = calculate_center_stats(ctx)
#             stats.update(analysis)
#         else:
#             stats = {"has_freeze": False, "has_heat_duration_breach": False}
#
#         return EvaluateColdChainSafetyResponse.from_context(ctx, stats)
