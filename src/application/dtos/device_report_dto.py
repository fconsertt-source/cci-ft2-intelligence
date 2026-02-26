from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass(frozen=True)
class ThermalExcursionDTO:
    timestamp: str
    temperature: float
    duration_minutes: float
    impact_level: str  # "SAFE", "PARTIAL", "DISCARD"

@dataclass(frozen=True)
class AdvisorySection:
    """
    Scientific advisory only — NEVER influences final_status.
    """
    freeze_events: int
    heat_events: int
    total_heat_hours: float
    max_temp_exceeded_count: int
    remaining_potency_estimate: float  # 0.0–100.0

@dataclass(frozen=True)
class ValidationProtocol:
    required: bool
    method: str
    timeframe_hours: int
    responsible: str
    documentation_required: bool

@dataclass(frozen=True)
class DeviceReportDTO:
    device_id: str
    vaccine_type: str
    total_records: int
    excursions: List[ThermalExcursionDTO]
    final_status: str  # ← Regulatory decision only: SAFE/PARTIAL/DISCARD
    scientific_rationale: str
    advisory_section: Optional[AdvisorySection] = None      # ← الحقل الجديد
    validation_required: Optional[ValidationProtocol] = None  # ← الحقل الجديد
