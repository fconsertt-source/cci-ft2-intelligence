"""
اختبارات ثوابت المجال — تضمن عدم كسر القواعد الأساسية
"""

from datetime import datetime

from src.domain.entities.vaccination_center import FreezeTolerance, VaccinationCenter


# helper dummy to mimic minimal interface expected by VaccinationCenter
class DummyEntry:
    """Minimal object with a ``temperature`` attribute used in tests."""

    def __init__(self, temp: float):
        self.temperature = temp


def test_initial_decision_is_no_data():
    """القرار الابتدائي يجب أن يكون NO_DATA"""
    center = VaccinationCenter(
        id="TEST",
        name="Test",
        device_ids=["D1"],
        temperature_ranges={"min": 2, "max": 8},
        decision_thresholds={},
    )
    assert center.decision == "NO_DATA"


def test_freeze_tolerance_policy_is_enforced():
    """سياسة ZERO_TOLERANCE يجب أن ترفض أي تجمد فوراً"""
    center = VaccinationCenter(
        id="TEST",
        name="Test",
        device_ids=["D1"],
        temperature_ranges={"min": 2, "max": 8},
        decision_thresholds={},
        freeze_tolerance=FreezeTolerance.ZERO_TOLERANCE,
    )
    entry = DummyEntry(-0.6)
    center.add_ft2_entry(entry)
    assert center.decision == "REJECTED_FREEZE_SENSITIVE"


def test_boundary_temperature_does_not_trigger_freeze():
    """درجة -0.5 بالضبط لا تُعتبر تجمداً (الشرط: < -0.5)"""
    center = VaccinationCenter(
        id="TEST",
        name="Test",
        device_ids=["D1"],
        temperature_ranges={"min": 2, "max": 8},
        decision_thresholds={},
        freeze_tolerance=FreezeTolerance.ZERO_TOLERANCE,
    )
    entry = DummyEntry(-0.5)
    center.add_ft2_entry(entry)
    assert center.decision != "REJECTED_FREEZE_SENSITIVE"
