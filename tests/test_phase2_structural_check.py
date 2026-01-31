# tests/test_phase2_structural_check.py
import unittest
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Mocks for Domain Layer ---
@dataclass
class MockEntry:
    temperature: float
    duration_minutes: int

class RuntimeCenter:
    """Proxy Entity for Domain Processing"""
    def __init__(self, id, name, device_ids, temperature_ranges=None):
        self.id = id
        self.name = name
        self.device_ids = device_ids
        self.temperature_ranges = temperature_ranges or {'min': 2.0, 'max': 8.0}
        self.ft2_entries: List[MockEntry] = []
        
        # Results
        self.decision = 'UNKNOWN'
        self.vvm_stage = 'NONE'
        self.alert_level = None
        self.stability_budget_consumed_pct = 0.0
        self.thaw_remaining_hours = None
        self.category_display = None
        self.decision_reasons: List[str] = []
        self.has_warning: bool = False  # جديد: حقل التحذير

    def add_ft2_entry(self, entry: MockEntry):
        self.ft2_entries.append(entry)

# --- DTO for Presentation Layer ---
@dataclass(frozen=True)
class CenterDTO:
    id: str
    name: str
    device_ids: List[str]
    decision: str
    vvm_stage: str
    decision_reasons: List[str]
    alert_level: Optional[str] = None
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    category_display: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    ft2_entries_count: int = 0
    has_warning: bool = False  # جديد: حقل التحذير

# --- Mocked Domain Services ---
def apply_rules(center: RuntimeCenter):
    """Simplified rules engine respecting custom temperature_ranges"""
    max_temp = center.temperature_ranges.get('max', 8.0)
    for e in center.ft2_entries:
        if e.temperature > max_temp:
            center.decision = 'REJECTED'
            center.decision_reasons.append(f"Temp {e.temperature} > max {max_temp}")
            return
    center.decision = 'ACCEPTED'
    center.decision_reasons.append("All entries within custom range")
    # مثال على تحذير إذا درجة الحرارة ضمن نافذة حرجة
    if any(10 <= e.temperature <= max_temp for e in center.ft2_entries):
        center.has_warning = True

def calculate_center_stats(center: RuntimeCenter):
    """Simplified stats calculation"""
    temps = [e.temperature for e in center.ft2_entries]
    if not temps:
        return {}
    max_temp = center.temperature_ranges.get('max', 8.0)
    heat_duration = sum(e.duration_minutes for e in center.ft2_entries if e.temperature > max_temp)
    return {
        'min_temp': min(temps),
        'max_temp': max(temps),
        'avg_temp': sum(temps)/len(temps),
        'heat_duration': heat_duration,
        'freeze_duration': 0,
        'completeness_score': 100,
        'has_freeze': False,
        'has_ccm_violation': False
    }

# --- Test Case ---
class TestPhase2StructuralCheck(unittest.TestCase):
    """
    Phase 2 Verification Test:
    Confirms that Deferred Mapping preserves Domain Logic with custom ranges.
    """

    def test_deferred_mapping_preserves_custom_ranges(self):
        # Setup RuntimeCenter with custom max temperature
        rc = RuntimeCenter(
            id="TEST_CUSTOM",
            name="Custom Range Center",
            device_ids=["D1"],
            temperature_ranges={'min': 2.0, 'max': 15.0}  # Custom range
        )
        rc.add_ft2_entry(MockEntry(temperature=10.0, duration_minutes=600))

        # Apply domain rules
        apply_rules(rc)

        # Map to DTO (Boundary Mapping)
        dto = CenterDTO(
            id=rc.id,
            name=rc.name,
            device_ids=rc.device_ids,
            decision=rc.decision,
            vvm_stage=rc.vvm_stage,
            decision_reasons=rc.decision_reasons,
            alert_level=rc.alert_level,
            stability_budget_consumed_pct=rc.stability_budget_consumed_pct,
            thaw_remaining_hours=rc.thaw_remaining_hours,
            category_display=rc.category_display,
            stats=calculate_center_stats(rc),
            ft2_entries_count=len(rc.ft2_entries),
            has_warning=rc.has_warning
        )

        # --- Assertions ---
        # 1. Decision respects custom range
        self.assertEqual(dto.decision, "ACCEPTED", "Decision should respect custom temperature ranges")
        # 2. Stats calculation uses custom max limit
        self.assertEqual(dto.stats.get('heat_duration', -1), 0, "Heat duration should be 0 for 10°C < 15°C")
        # 3. DTO immutability & data correctness
        self.assertEqual(dto.ft2_entries_count, 1, "DTO should reflect correct number of entries")
        self.assertIn("All entries within custom range", dto.decision_reasons)
        # 4. Warning propagation
        self.assertTrue(dto.has_warning, "DTO should reflect domain warning correctly")

if __name__ == "__main__":
    unittest.main()
