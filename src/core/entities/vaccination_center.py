# vaccination_center.py (مُحسّن)
from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum, auto

class FreezeTolerance(Enum):
    ZERO_TOLERANCE = auto()      # أي تجميد = رفض
    SINGLE_SHOCK = auto()        # صدمة واحدة قصيرة
    MULTIPLE_SHOCKS = auto()     # متعدد مع قيود

@dataclass
class VaccinationCenter:
    id: str
    name: str
    device_ids: List[str]
    temperature_ranges: Dict[str, float]
    decision_thresholds: Dict[str, Any]
    
    # حقول اختيارية / محسوبة
    ft2_entries: List[Any] = field(default_factory=list)
    decision: str = "NO_DATA"
    vvm_stage: str = "NONE"
    
    freeze_tolerance: FreezeTolerance = FreezeTolerance.ZERO_TOLERANCE
    freeze_event_counter: Dict[str, int] = field(default_factory=dict)  # device_id -> count
    
    def add_ft2_entry(self, entry):
        """إضافة إدخال FT2 وتحديث القرار"""
        self.ft2_entries.append(entry)
        self._update_decision()

    def _apply_zero_tolerance(self):
        self.decision = "REJECTED_FREEZE_SENSITIVE"
        self.vvm_stage = "D"

    def _reject_freeze_sensitive(self):
        self.decision = "REJECTED_FREEZE_SENSITIVE"
        self.vvm_stage = "D"

    def _update_decision(self):
        """تحديث القرار"""
        # حساب أحداث التجميد
        freeze_events = self._count_freeze_events()
        
        # تطبيق سياسة التجميد
        if self.freeze_tolerance == FreezeTolerance.ZERO_TOLERANCE:
            if freeze_events["total"] > 0:
                self._apply_zero_tolerance()
    
    def _count_freeze_events(self) -> Dict[str, Any]:
        """عد أحداث التجميد وتجميع مددها"""
        events = {
            "total": 0,
            "durations": [],
            "by_device": {}
        }
        
        for entry in self.ft2_entries:
            if hasattr(entry, 'temperature') and entry.temperature < -0.5:
                events["total"] += 1
                duration = getattr(entry, 'duration_minutes', 15)
                events["durations"].append(duration)
                
                # تجميع حسب الجهاز
                device_id = getattr(entry, 'device_id', 'unknown')
                events["by_device"][device_id] = events["by_device"].get(device_id, 0) + 1
        
        return events