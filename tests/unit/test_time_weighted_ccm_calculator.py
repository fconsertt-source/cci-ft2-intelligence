# tests/unit/test_time_weighted_ccm_calculator.py
"""
اختبارات وحدة لـ TimeWeightedCcmCalculator.

تغطي:
- الحالات الحدية
- صحة AUC الموزون زمنياً
- الاستقلالية عن HER
- التوافق مع ccm_calculator.py الأصلي (TIME_UNIT = minutes)
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.domain.calculators.time_weighted_ccm_calculator import \
    TimeWeightedCcmCalculator
from src.domain.entities.temperature_reading import TemperatureReading

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_readings(
    temps: list[float],
    start: datetime | None = None,
    interval_minutes: float = 60.0,
    vaccine_id: str = "VAC-CCM",
) -> list[TemperatureReading]:
    if start is None:
        start = datetime(2025, 1, 1, 0, 0, 0)
    return [
        TemperatureReading(
            vaccine_id=vaccine_id,
            value=t,
            recorded_at=start + timedelta(minutes=i * interval_minutes),
        )
        for i, t in enumerate(temps)
    ]


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------


class TestTimeWeightedCcmCalculatorEdgeCases:

    def test_empty_readings_returns_zeros(self):
        calc = TimeWeightedCcmCalculator()
        result = calc.calculate([])
        assert result.ccm_delta == 0.0
        assert result.ccm_auc == 0.0
        assert result.total_duration_minutes == 0.0
        assert result.readings_count == 0

    def test_single_reading_returns_zeros(self):
        calc = TimeWeightedCcmCalculator()
        result = calc.calculate(make_readings([10.0]))
        assert result.ccm_delta == 0.0
        assert result.ccm_auc == 0.0

    def test_duplicate_timestamps_ignored(self):
        t = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 20.0, t),
            TemperatureReading("V", 25.0, t),
        ]
        calc = TimeWeightedCcmCalculator()
        result = calc.calculate(readings)
        assert result.ccm_auc == 0.0
        assert result.total_duration_minutes == 0.0


# ---------------------------------------------------------------------------
# AUC correctness — TIME_UNIT = minutes
# ---------------------------------------------------------------------------


class TestTimeWeightedCcmCalculatorAUC:

    def test_constant_temp_above_base_60min(self):
        """
        درجة ثابتة = 10°C، base = 8°C، مدة = 60 دقيقة.
        AUC = (10-8) × 60 = 120 degree-minutes.
        """
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([10.0, 10.0], interval_minutes=60.0)
        result = calc.calculate(readings)

        assert result.ccm_auc == pytest.approx(120.0, rel=1e-6)
        assert result.total_duration_minutes == pytest.approx(60.0, rel=1e-6)

    def test_below_base_temp_no_auc(self):
        """
        درجة أقل من base_temp → AUC = 0.
        """
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([4.0, 6.0, 7.0], interval_minutes=30.0)
        result = calc.calculate(readings)

        assert result.ccm_auc == 0.0

    def test_exactly_at_base_temp_no_auc(self):
        """عند base_temp بالضبط → لا تراكم."""
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([8.0, 8.0], interval_minutes=120.0)
        result = calc.calculate(readings)

        assert result.ccm_auc == 0.0

    def test_auc_trapezoidal_rising_temp(self):
        """
        قراءتان: 8°C ثم 12°C، مدة 60 دقيقة.
        AUC = ((0 + 4) / 2) × 60 = 120 degree-minutes.
        """
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([8.0, 12.0], interval_minutes=60.0)
        result = calc.calculate(readings)

        assert result.ccm_auc == pytest.approx(120.0, rel=1e-6)

    def test_total_duration_accumulates_correctly(self):
        """المدة الكلية = مجموع جميع الفترات."""
        calc = TimeWeightedCcmCalculator()
        # 4 قراءات → 3 فترات × 30 دقيقة = 90 دقيقة
        readings = make_readings([5.0, 5.0, 5.0, 5.0], interval_minutes=30.0)
        result = calc.calculate(readings)

        assert result.total_duration_minutes == pytest.approx(90.0, rel=1e-6)

    def test_auc_per_hour_property(self):
        """
        AUC = 120 degree-min، duration = 60 min → per_hour = 120.
        """
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([10.0, 10.0], interval_minutes=60.0)
        result = calc.calculate(readings)

        assert result.auc_per_hour == pytest.approx(120.0, rel=1e-6)

    def test_has_heat_exposure_true_above_base(self):
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([10.0, 12.0], interval_minutes=60.0)
        result = calc.calculate(readings)
        assert result.has_heat_exposure is True

    def test_has_heat_exposure_false_below_base(self):
        calc = TimeWeightedCcmCalculator(base_temp=8.0)
        readings = make_readings([4.0, 6.0], interval_minutes=60.0)
        result = calc.calculate(readings)
        assert result.has_heat_exposure is False


# ---------------------------------------------------------------------------
# Delta correctness
# ---------------------------------------------------------------------------


class TestTimeWeightedCcmCalculatorDelta:

    def test_delta_below_threshold_ignored(self):
        """تغيير أقل من threshold لا يُحسب."""
        calc = TimeWeightedCcmCalculator(threshold=2.0)
        readings = make_readings([10.0, 11.0])  # فرق = 1.0 < 2.0
        result = calc.calculate(readings)
        assert result.ccm_delta == 0.0

    def test_delta_above_threshold_counted(self):
        """تغيير أكبر من threshold يُحسب."""
        calc = TimeWeightedCcmCalculator(threshold=1.0)
        readings = make_readings([10.0, 13.0])  # فرق = 3.0 > 1.0
        result = calc.calculate(readings)
        assert result.ccm_delta == pytest.approx(3.0, rel=1e-6)

    def test_delta_cumulates_over_multiple_readings(self):
        """تراكم Delta عبر قراءات متعددة."""
        calc = TimeWeightedCcmCalculator(threshold=1.0)
        # 10→13 (+3), 13→15 (+2), 15→17 (+2) = 7.0
        readings = make_readings([10.0, 13.0, 15.0, 17.0])
        result = calc.calculate(readings)
        assert result.ccm_delta == pytest.approx(7.0, rel=1e-6)


# ---------------------------------------------------------------------------
# unsorted input
# ---------------------------------------------------------------------------


class TestTimeWeightedCcmCalculatorOrdering:

    def test_unsorted_readings_same_result(self):
        calc = TimeWeightedCcmCalculator()
        t0 = datetime(2025, 6, 1)
        sorted_r = [
            TemperatureReading("V", 5.0, t0),
            TemperatureReading("V", 12.0, t0 + timedelta(hours=1)),
            TemperatureReading("V", 9.0, t0 + timedelta(hours=2)),
        ]
        shuffled = [sorted_r[2], sorted_r[0], sorted_r[1]]

        r_sorted = calc.calculate(sorted_r)
        r_shuffled = calc.calculate(shuffled)

        assert r_sorted.ccm_auc == pytest.approx(r_shuffled.ccm_auc, rel=1e-9)
        assert r_sorted.ccm_delta == pytest.approx(r_shuffled.ccm_delta, rel=1e-9)


# ---------------------------------------------------------------------------
# independence from HER
# ---------------------------------------------------------------------------


class TestCcmHerIndependence:

    def test_ccm_does_not_import_her(self):
        """التحقق من أن TimeWeightedCcmCalculator لا يستورد شيئاً من HER."""
        import importlib
        import sys

        mod_name = "src.domain.calculators.time_weighted_ccm_calculator"
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
        else:
            mod = importlib.import_module(mod_name)

        source_file = mod.__file__
        with open(source_file) as f:
            content = f.read().lower()

        assert "q10_her" not in content
        assert "herresult" not in content
        assert "vvmq10model" not in content
