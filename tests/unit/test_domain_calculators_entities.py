# tests/unit/test_domain_calculators_entities.py
"""اختبارات تغطية لـ Q10ThermalCalculator و FT2Entry و HERCalculator"""

from src.domain.calculators.her_calculator import HERCalculator
from src.domain.calculators.q10_thermal_calculator import Q10ThermalCalculator
from src.domain.entities.ft2_entry import FT2Entry
from src.domain.value_objects.vaccine_specification import VaccineSpecification

# ---------------------------------------------------------------------------
# HERCalculator
# ---------------------------------------------------------------------------


class TestHERCalculator:
    def setup_method(self):
        self.calc = HERCalculator()

    def test_zero_full_duration_returns_zero(self):
        assert self.calc.calculate(60, 0) == 0.0

    def test_negative_full_duration_returns_zero(self):
        assert self.calc.calculate(60, -10) == 0.0

    def test_normal_ratio(self):
        assert self.calc.calculate(30, 60) == 0.5

    def test_capped_at_one(self):
        assert self.calc.calculate(120, 60) == 1.0

    def test_full_exposure(self):
        assert self.calc.calculate(60, 60) == 1.0

    def test_zero_exposure(self):
        assert self.calc.calculate(0, 60) == 0.0


# ---------------------------------------------------------------------------
# Q10ThermalCalculator
# ---------------------------------------------------------------------------


def make_spec(
    min_temp=2.0,
    max_temp=8.0,
    freeze_sensitive=True,
    excursion_time_limit=4.0,
):
    return VaccineSpecification(
        vaccine_type="TestVaccine",
        min_temp=min_temp,
        max_temp=max_temp,
        freeze_sensitive=freeze_sensitive,
        excursion_time_limit=excursion_time_limit,
    )


class TestQ10ThermalCalculator:
    def setup_method(self):
        self.calc = Q10ThermalCalculator()

    def test_within_range_returns_safe(self):
        spec = make_spec()
        assert self.calc.evaluate(5.0, 60, spec) == "SAFE"

    def test_freezing_sensitive_discard(self):
        spec = make_spec(freeze_sensitive=True)
        assert self.calc.evaluate(-1.0, 60, spec) == "DISCARD"

    def test_high_temp_long_duration_discard(self):
        spec = make_spec(excursion_time_limit=2.0)
        # duration_hours = 180/60 = 3.0 > 2.0
        assert self.calc.evaluate(10.0, 180, spec) == "DISCARD"

    def test_high_temp_medium_duration_partial(self):
        spec = make_spec(excursion_time_limit=4.0)
        # duration_hours = 150/60 = 2.5 > 4/2=2.0 but < 4.0
        assert self.calc.evaluate(10.0, 150, spec) == "PARTIAL"

    def test_high_temp_short_duration_safe(self):
        spec = make_spec(excursion_time_limit=4.0)
        # duration_hours = 30/60 = 0.5 < 4/2=2.0
        assert self.calc.evaluate(10.0, 30, spec) == "SAFE"

    def test_below_min_not_freezing_discard(self):
        spec = make_spec(min_temp=2.0, freeze_sensitive=False, excursion_time_limit=2.0)
        assert self.calc.evaluate(1.0, 180, spec) == "DISCARD"


# ---------------------------------------------------------------------------
# FT2Entry
# ---------------------------------------------------------------------------


def make_entry(**kwargs):
    defaults = dict(
        day_number=1,
        date="2024-01-01",
        temperatures={"min": 2.0, "max": 8.0, "avg": 5.0},
        alarms={"0": {"t_acc": 0}, "1": {"t_acc": 0}},
        sensor_timeout={},
        events=0,
    )
    defaults.update(kwargs)
    return FT2Entry(**defaults)


class TestFT2Entry:
    def test_has_freezing_true(self):
        entry = make_entry(alarms={"0": {"t_acc": 30}, "1": {"t_acc": 0}})
        assert entry.has_freezing is True

    def test_has_freezing_false(self):
        entry = make_entry()
        assert entry.has_freezing is False

    def test_has_ft2_tacc_alarm_true(self):
        entry = make_entry(alarms={"0": {"t_acc": 0}, "1": {"t_acc": 700}})
        assert entry.has_ft2_tacc_alarm is True

    def test_has_ft2_tacc_alarm_false(self):
        entry = make_entry()
        assert entry.has_ft2_tacc_alarm is False

    def test_freeze_minutes(self):
        entry = make_entry(alarms={"0": {"t_acc": 45}, "1": {"t_acc": 0}})
        assert entry.freeze_minutes == 45

    def test_ccm_minutes(self):
        entry = make_entry(alarms={"0": {"t_acc": 0}, "1": {"t_acc": 500}})
        assert entry.ccm_minutes == 500

    def test_temperature_range(self):
        entry = make_entry(temperatures={"min": 2.0, "max": 8.0, "avg": 5.0})
        assert entry.temperature_range == 6.0

    def test_to_dict_contains_all_keys(self):
        entry = make_entry()
        d = entry.to_dict()
        expected = {
            "day_number",
            "date",
            "temperatures",
            "alarms",
            "sensor_timeout",
            "events",
            "has_freezing",
            "has_ft2_tacc_alarm",
            "freeze_minutes",
            "ccm_minutes",
            "temperature_range",
        }
        assert expected.issubset(d.keys())
