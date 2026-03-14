# tests/unit/test_vaccination_center_coverage.py
"""اختبارات تغطية لـ VaccinationCenter"""

from src.domain.entities.ft2_entry import FT2Entry
from src.domain.entities.vaccination_center import VaccinationCenter


def make_center(**kwargs):
    defaults = dict(
        id="CTR-001",
        name="مركز الاختبار",
        device_ids=["DEV-001"],
        temperature_ranges={"min": 2.0, "max": 8.0},
        decision_thresholds={"freeze_threshold": 0.0, "ccm_limit": 600},
    )
    defaults.update(kwargs)
    return VaccinationCenter(**defaults)


def make_entry(temp_min=3.0, temp_max=7.0, alarm0=0, alarm1=0):
    return FT2Entry(
        day_number=1,
        date="2024-01-01",
        temperatures={
            "min": temp_min,
            "max": temp_max,
            "avg": (temp_min + temp_max) / 2,
        },
        alarms={"0": {"t_acc": alarm0}, "1": {"t_acc": alarm1}},
        sensor_timeout={},
        events=0,
    )


class TestVaccinationCenterFreezeViolation:
    def test_add_freeze_entry_sets_rejected(self):
        center = make_center()
        entry = make_entry(temp_min=-1.0)
        center.add_ft2_entry(entry)
        assert center.decision == "REJECTED_FREEZE_SENSITIVE"

    def test_add_freeze_entry_increments_counter(self):
        center = make_center()
        entry = make_entry(temp_min=-1.0)
        center.add_ft2_entry(entry)
        assert center.count_freeze_events == 1

    def test_add_freeze_entry_sets_vvm_stage_d(self):
        center = make_center()
        entry = make_entry(temp_min=-1.0)
        center.add_ft2_entry(entry)
        assert center.vvm_stage == "D"

    def test_normal_entry_no_violation(self):
        center = make_center()
        entry = make_entry(temp_min=3.0)
        center.add_ft2_entry(entry)
        assert center.decision == "NO_DATA"
        assert center.count_freeze_events == 0

    def test_has_freezing_flag_triggers_violation(self):
        center = make_center()
        entry = make_entry(temp_min=3.0, alarm0=30)  # has_freezing=True
        center.add_ft2_entry(entry)
        assert center.decision == "REJECTED_FREEZE_SENSITIVE"


class TestVaccinationCenterDecisionProperty:
    def test_decision_getter(self):
        center = make_center()
        assert center.decision == "NO_DATA"

    def test_decision_setter(self):
        center = make_center()
        center.decision = "APPROVED"
        assert center.decision == "APPROVED"


class TestVaccinationCenterFreezeEvents:
    def test_freeze_events_empty(self):
        center = make_center()
        events = center.freeze_events
        assert events["total"] == 0

    def test_freeze_events_with_freeze_entry(self):
        center = make_center()
        center.ft2_entries.append(make_entry(temp_min=-1.0, alarm0=30))
        events = center.freeze_events
        assert events["total"] == 1

    def test_has_freeze_false(self):
        center = make_center()
        assert center.has_freeze is False

    def test_has_freeze_true(self):
        center = make_center()
        center.ft2_entries.append(make_entry(temp_min=-1.0, alarm0=30))
        assert center.has_freeze is True


class TestVaccinationCenterCCM:
    def test_ccm_violations_empty(self):
        center = make_center()
        center.ft2_entries.append(make_entry(alarm1=100))
        assert center.ccm_violations == []

    def test_ccm_violations_found(self):
        center = make_center()
        center.ft2_entries.append(make_entry(alarm1=700))
        assert len(center.ccm_violations) == 1

    def test_total_ccm_minutes(self):
        center = make_center()
        center.ft2_entries.append(make_entry(alarm1=300))
        center.ft2_entries.append(make_entry(alarm1=200))
        assert center.total_ccm_minutes == 500


class TestCountFreezeEvents:
    def test_count_freeze_events_no_entries(self):
        center = make_center()
        result = center._count_freeze_events()
        assert result["total_freeze_events"] == 0
        assert result["by_device"] == {}

    def test_count_freeze_events_with_freeze(self):
        center = make_center()
        center.ft2_entries.append(make_entry(temp_min=-1.0, alarm0=30))
        result = center._count_freeze_events()
        assert result["total_freeze_events"] == 1


class TestVaccinationCenterMissingLines:
    def test_entry_with_no_temp_and_no_freeze_returns_early(self):
        """السطر 65 — entry بدون temperature ولا has_freezing"""
        center = make_center()

        class EmptyEntry:
            pass

        entry = EmptyEntry()
        center.add_ft2_entry(entry)
        assert center.decision == "NO_DATA"

    def test_count_freeze_events_with_devices(self):
        """السطر 98-112 — devices loop"""
        from unittest.mock import MagicMock

        center = make_center()
        device = MagicMock()
        device.get_temperature_history.return_value = [
            {"is_freeze_event": True},
            {"is_freeze_event": False},
        ]
        center.devices = {"DEV-001": device}
        result = center._count_freeze_events()
        assert result["total_freeze_events"] == 1
        assert result["by_device"]["DEV-001"] == 1

    def test_freeze_events_with_device_id(self):
        """السطر 147 — by_device في freeze_events"""
        center = make_center()
        entry = make_entry(temp_min=-1.0, alarm0=30)

        class EntryWithDevice(FT2Entry.__class__):
            pass

        entry.device_id = "DEV-001"
        center.ft2_entries.append(entry)
        events = center.freeze_events
        assert events["by_device"].get("DEV-001") == 1
