# src/domain/entities/vaccination_center.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from src.domain.entities.ft2_entry import (  # افتراض وجود هذا الكيان في المسار الجديد
    FT2Entry,
)

from .archive_record import ArchiveRecord, ArchiveStatus


class FreezeTolerance(Enum):
    ZERO_TOLERANCE = auto()  # أي تجميد = رفض
    SINGLE_SHOCK = auto()  # صدمة واحدة قصيرة
    MULTIPLE_SHOCKS = auto()  # متعدد مع قيود


@dataclass
class VaccinationCenter:
    """كيان مركز التطعيم – يحتوي على البيانات فقط، مع خصائص محسوبة"""

    id: str
    name: str
    device_ids: List[str]
    temperature_ranges: Dict[str, float]
    decision_thresholds: Dict[str, Any]

    # الإدخالات (يفضل أن تكون من نوع FT2Entry)
    ft2_entries: List[FT2Entry] = field(default_factory=list)

    # سياسة تحمل التجميد (قد تُقرأ من ملف الإعدادات)
    freeze_tolerance: FreezeTolerance = FreezeTolerance.ZERO_TOLERANCE

    # map of device_id -> device object; used in new counting logic (Phase 5 planning)
    # kept empty by default so legacy callers are unaffected.
    devices: Dict[str, Any] = field(default_factory=dict)

    # internal state that is not part of construction arguments
    _decision: str = field(default="NO_DATA", init=False)
    # keep a numeric counter for freeze violations; method _count_freeze_events is
    # a separate helper used by tests, so avoid name collision
    _freeze_event_count: int = field(default=0, init=False)
    # stage may be assigned by rules logic or internally updated
    vvm_stage: Optional[str] = None

    def add_ft2_entry(self, entry: FT2Entry):
        """إضافة مدخل حراري وتحديث القرار فوراً إذا لزم الأمر"""
        self.ft2_entries.append(entry)
        self._evaluate_freeze_violation(entry)

    def _evaluate_freeze_violation(self, entry: FT2Entry):
        # determine if this entry represents a freeze event.  historically
        # the tests used a simple ``entry.temperature`` attribute, but the
        # canonical FT2Entry class has a more complex structure.  we'll
        # support both to ease migration (Phase 1 requirement).
        temp = getattr(entry, "temperature", None)
        has_freeze = getattr(entry, "has_freezing", False)
        if temp is None:
            # try to infer from temperatures dict if present
            temps = getattr(entry, "temperatures", {}) or {}
            temp = temps.get("min", None)
        if temp is None and not has_freeze:
            # nothing we can inspect; give up
            return

        violation = False
        if temp is not None and temp < -0.5:
            violation = True
        if has_freeze:
            violation = True

        if violation and self.freeze_tolerance == FreezeTolerance.ZERO_TOLERANCE:
            self._decision = "REJECTED_FREEZE_SENSITIVE"
            # increment counter and update stage as quick heuristic
            self._freeze_event_count += 1
            # when a freeze-sensitive rejection occurs we consider VVM stage D
            self.vvm_stage = "D"

    def _count_freeze_events(self) -> Dict:
        """
        Counts freeze events across all associated devices.

        The method is intentionally conservative in responsibility to avoid
        turning the entity into a reporting helper.  A simple dictionary is
        returned that callers (tests or services) can format however they
        choose.

        NOTE:
        Aggregation by device is temporary for backward compatibility.
        TODO: consider moving aggregation outside entity (Phase 5)
        """
        total_events = 0
        by_device: Dict[str, int] = {}

        # new behaviour - iterate over self.devices if any have been attached
        if hasattr(self, "devices") and self.devices:
            for device_id, device in self.devices.items():
                history = []
                try:
                    history = device.get_temperature_history() or []
                except Exception:
                    # defensive: if the object doesn't provide expected API
                    history = []

                device_events = 0
                for record in history:
                    if record.get("is_freeze_event"):
                        device_events += 1

                by_device[device_id] = device_events
                total_events += device_events
        else:
            # fallback to legacy ft2_entries (existing tests rely on this)
            for entry in self.ft2_entries:
                # check both forms of freeze markers
                temp = getattr(entry, "temperature", None)
                if temp is None:
                    temps = getattr(entry, "temperatures", {}) or {}
                    temp = temps.get("min", 0)
                is_freeze = False
                if temp is not None and temp < -0.5:
                    is_freeze = True
                if getattr(entry, "has_freezing", False):
                    is_freeze = True
                if is_freeze:
                    total_events += 1
                    device_id = getattr(entry, "device_id", None)
                    if device_id:
                        by_device[device_id] = by_device.get(device_id, 0) + 1

        return {
            "total_freeze_events": total_events,
            "by_device": by_device,
        }

    @property
    def freeze_events(self) -> Dict[str, Any]:
        """تجميع أحداث التجميد من إدخالات FT2"""
        events = {"total": 0, "durations": [], "by_device": {}}
        for entry in self.ft2_entries:
            if getattr(
                entry,
                "has_freezing",
                getattr(
                    entry,
                    "temperature",
                    getattr(entry, "temperatures", {}).get("min", 0),
                )
                < -0.5,
            ):
                events["total"] += 1
                events["durations"].append(getattr(entry, "freeze_minutes", None))
                device_id = getattr(entry, "device_id", None)
                if device_id:
                    events["by_device"][device_id] = (
                        events["by_device"].get(device_id, 0) + 1
                    )
        return events

    @property
    def decision(self) -> str:
        """Current rejection/acceptance decision of the center."""
        return self._decision

    @decision.setter
    def decision(self, value: str):
        """Set the decision state of the center."""
        self._decision = value

    @property
    def count_freeze_events(self) -> int:
        """Total number of freeze violations recorded internally."""
        return self._freeze_event_count

    @property
    def has_freeze(self) -> bool:
        return self.freeze_events["total"] > 0

    @property
    def ccm_violations(self) -> List[FT2Entry]:
        """إدخالات تحتوي على انتهاكات CCM"""
        return [entry for entry in self.ft2_entries if entry.has_ccm_violation]

    @property
    def total_ccm_minutes(self) -> int:
        """إجمالي دقائق CCM عبر جميع الإدخالات"""
        return sum(entry.ccm_minutes for entry in self.ft2_entries)

    # يمكن إضافة المزيد من الخصائص المحسوبة حسب الحاجة
