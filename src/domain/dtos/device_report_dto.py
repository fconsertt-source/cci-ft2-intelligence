# src/domain/dtos/device_report_dto.py
#!/usr/bin/env python3
"""Device Report DTO — كائن نقل بيانات التقرير (عقد صارم)"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ReportStatus(Enum):
    """حالة الجهاز النهائية"""

    SAFE = "safe"
    WARNING = "warning"
    DISCARD = "discard"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ThermalExcursionDTO:
    """انحراف حراري واحد"""

    timestamp: str
    temperature: float
    duration_minutes: float
    impact_level: str


@dataclass(frozen=True)
class AdvisorySection:
    """قسم التوصيات"""

    freeze_events: int
    heat_events: int
    total_heat_hours: float
    max_temp_exceeded_count: int
    remaining_potency_estimate: float


@dataclass(frozen=True)
class ValidationProtocol:
    """بروتوكول التحقق"""

    required: bool
    method: str
    timeframe_hours: int
    responsible: str
    documentation_required: bool


@dataclass(frozen=True)
class DeviceReportDTO:
    """
    عقد تقرير الجهاز - صارم وغير قابل للتعديل

    ⚠️ أي تغيير في هذا العقد يتطلب:
    1. تحديث Contract Test
    2. تحديث Golden Master
    3. توثيق في CHANGELOG
    """

    device_id: str
    vaccine_type: str
    total_records: int
    excursions: Tuple[ThermalExcursionDTO, ...]  # ✅ tuple وليس list
    final_status: str
    scientific_rationale: str
    advisory_section: Optional[AdvisorySection] = None
    validation_required: Optional[ValidationProtocol] = None
    generated_at: Optional[str] = None
    operator: Optional[str] = None
    cycle_id: Optional[str] = None

    # ✅ حقول إضافية للاستراتيجيات
    status: Optional[ReportStatus] = None
    readings: Tuple = field(default_factory=tuple)
    ledger_hash: str = ""

    def __post_init__(self):
        """التحقق من الصحة عند الإنشاء"""
        if self.generated_at is None:
            object.__setattr__(
                self, "generated_at", datetime.now(timezone.utc).isoformat()
            )
        if not self.device_id or not self.device_id.strip():
            raise ValueError("device_id cannot be empty")
        if self.ledger_hash and len(self.ledger_hash) != 64:
            raise ValueError("ledger_hash must be SHA-256 (64 chars)")

    def get_batch_counts(self) -> Dict[str, int]:
        """عدّ الدفعات حسب الحالة"""
        counts = {"safe": 0, "warning": 0, "discard": 0}
        for e in self.excursions:
            # ✅ بدون مسافات زائدة
            if e.impact_level == "SAFE":
                counts["safe"] += 1
            elif e.impact_level == "PARTIAL":
                counts["warning"] += 1
            elif e.impact_level == "DISCARD":
                counts["discard"] += 1
        return counts
