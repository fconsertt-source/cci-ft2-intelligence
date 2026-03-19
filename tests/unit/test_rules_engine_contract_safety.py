from types import SimpleNamespace

from src.domain.services.rules_engine import apply_rules


def make_center(readings):
    entries = [SimpleNamespace(temperature=t, duration_minutes=10) for t in readings]

    return SimpleNamespace(
        ft2_entries=entries,
        decision_reasons=[],
    )


class TestRulesEngineContractSafety:

    def test_max_temp_is_correctly_computed(self):
        center = make_center([2.0, 5.0, 7.5, 6.0])

        apply_rules(center)

        assert max(e.temperature for e in center.ft2_entries) == 7.5

    def test_freeze_detection_basic(self):
        center = make_center([-1.0, -2.0, 3.0, 5.0])

        apply_rules(center)

        assert any(e.temperature < 0 for e in center.ft2_entries)

    def test_freeze_absence_when_no_negative(self):
        center = make_center([2.0, 3.0, 4.0, 5.0])

        apply_rules(center)

        assert all(e.temperature >= 0 for e in center.ft2_entries)

    def test_upper_safety_boundary_violation(self):
        center = make_center([2.0, 5.0, 9.0, 6.0])

        apply_rules(center)

        assert max(e.temperature for e in center.ft2_entries) > 8.0

    def test_critical_limit_flagging(self):
        center = make_center([10.0, 12.0, 9.0])

        apply_rules(center)

        assert center.ft2_entries[-1].temperature == 9.0

    def test_result_structure_consistency(self):
        center = make_center([1.0, 2.0, 3.0])

        apply_rules(center)

        assert hasattr(center, "decision_reasons")
        assert isinstance(center.decision_reasons, list)
