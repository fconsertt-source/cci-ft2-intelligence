import pytest
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.entities.vaccination_center import VaccinationCenter
from src.core.services.rules_engine import apply_rules
from src.core.enums.vvm_stage import VVMStage
from src.core.calculators.vvm_q10_model import VVMQ10Model

@dataclass
class MockEntry:
    """Mock for FT2 device entry"""
    temperature: float
    duration_minutes: float

def run_vvm_simulation(entries: List[MockEntry], her: float = 0.0, critical_limit: float = 50.0) -> VaccinationCenter:
    """Helper to run a simulation and return the center after rule application"""
    center = VaccinationCenter(
        id="SIM-TEST",
        name="VVM Test Center",
        device_ids=["D1"],
        temperature_ranges={"min": 2, "max": 8},
        # نرفع الحدود هنا للسماح برؤية مراحل VVM دون رفض فوري بسبب القواعد القديمة
        decision_thresholds={"ccm_limit": 100000} 
    )
    # تعيين حد حراري حرج للمحاكاة (افتراضي 50 لتجنب التداخل مع VVM)
    setattr(center, 'critical_temp_limit', critical_limit)
    
    for entry in entries:
        center.add_ft2_entry(entry)
    
    # Calculate max_temp from entries for rules engine
    max_temp = max([e.temperature for e in entries]) if entries else 0.0
    
    apply_rules(center, extra_stats={'her': her, 'max_temp': max_temp})
    return center

class TestVVMBiologicalScenarios:
    """
    Formalized VVM simulation scenarios converted to automated tests.
    Ensures that biological degradation logic aligns with decisional rules.
    """

    def test_ideal_condition_stays_safe(self):
        # 30 days at 5°C
        entries = [MockEntry(5.0, 30 * 24 * 60)]
        center = run_vvm_simulation(entries, her=0.0)
        
        assert center.decision == "ACCEPTED"
        assert center.vvm_stage == VVMStage.NONE

    def test_minor_heat_exposure_threshold(self):
        # 1.5 days at 9°C (Below VVM Stage A threshold)
        entries = [MockEntry(9.0, 1.5 * 24 * 60)]
        # Assuming HER calculation from UseCase would be around 0.05
        center = run_vvm_simulation(entries, her=0.05)
        
        assert center.decision == "ACCEPTED"
        assert center.vvm_stage == VVMStage.NONE

    def test_vvm_stage_a_transition(self):
        # HER >= 0.1 triggers Stage A
        entries = [MockEntry(15.0, 3 * 24 * 60)]
        center = run_vvm_simulation(entries, her=0.15)
        
        assert center.vvm_stage == VVMStage.A
        assert center.decision == "ACCEPTED" # Still usable but with warning

    def test_vvm_stage_b_transition(self):
        # HER >= 0.4 triggers Stage B
        entries = [MockEntry(20.0, 7 * 24 * 60)]
        center = run_vvm_simulation(entries, her=0.45)
        
        assert center.vvm_stage == VVMStage.B
        assert center.decision == "ACCEPTED"

    def test_vvm_stage_c_impending_expiry(self):
        # HER >= 0.7 triggers Stage C
        entries = [MockEntry(12.0, 12 * 24 * 60)]
        center = run_vvm_simulation(entries, her=0.75)
        
        assert center.vvm_stage == VVMStage.C
        assert center.decision == "ACCEPTED"

    def test_vvm_stage_d_total_loss_discard(self):
        # HER >= 1.0 triggers Stage D and REJECTED
        entries = [MockEntry(16.0, 21 * 24 * 60)]
        center = run_vvm_simulation(entries, her=1.1)
        
        assert center.vvm_stage == VVMStage.D
        assert center.decision == "REJECTED_HEAT_C"

    def test_severe_heat_spike_discard(self):
        # Temperature spike > 10°C (Default critical limit)
        entries = [MockEntry(35.0, 120)] # 2 hours at 35°C
        # Even if HER is low, max_temp rule should trigger if we set a realistic limit
        center = run_vvm_simulation(entries, her=0.05, critical_limit=10.0)
        
        assert center.decision == "REJECTED_HEAT_C"

    def test_combined_freeze_and_heat_stress(self):
        # Freeze violation + Heat Stress (Stage B)
        entries = [
            MockEntry(-2.0, 60),          # Freeze
            MockEntry(15.0, 7 * 24 * 60) # Heat
        ]
        center = run_vvm_simulation(entries, her=0.45)
        
        # Priority: Freeze usually triggers first or takes precedence
        assert center.decision == "REJECTED_FREEZE"
        assert center.vvm_stage == VVMStage.B

if __name__ == "__main__":
    pytest.main([__file__])
