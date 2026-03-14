# tests/unit/test_q10_her_calculator.py
"""
اختبارات وحدة لـ Q10HerCalculator.

تغطي:
- الحالات الحدية (0 قراءة، قراءة واحدة)
- الحرارة الطبيعية (لا انحلال)
- الحرارة فوق المرجع (انحلال متسارع)
- الحرارة تحت المرجع (انحلال متباطئ)
- الاستقلالية عن CCM (لا تأثير متبادل)
- توافق القيم مع نموذج Q10 العلمي
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.domain.calculators.q10_her_calculator import (
    Q10HerCalculator,
)
from src.domain.entities.temperature_reading import TemperatureReading


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_readings(
    temps: list[float],
    start: datetime | None = None,
    interval_hours: float = 1.0,
    vaccine_id: str = "VAC-001",
) -> list[TemperatureReading]:
    """بناء قائمة قراءات من درجات حرارة وفترات زمنية مع تحديد المدة."""
    if start is None:
        start = datetime(2025, 1, 1, 0, 0, 0)
    
    readings = []
    for i, t in enumerate(temps):
        readings.append(TemperatureReading(
            vaccine_id=vaccine_id,
            value=t,
            recorded_at=start + timedelta(hours=i * interval_hours),
            duration_hours=interval_hours,
        ))
    return readings


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

class TestQ10HerCalculatorEdgeCases:

    def test_empty_readings_returns_zero(self):
        calc = Q10HerCalculator()
        result = calc.calculate([])
        assert result.cumulative_degradation_hours == 0.0
        assert result.her_ratio == 0.0
        assert result.readings_count == 0

    def test_single_reading_returns_zero(self):
        calc = Q10HerCalculator()
        readings = make_readings([10.0])
        result = calc.calculate(readings)
        assert result.cumulative_degradation_hours == 0.0
        assert result.her_ratio == 0.0
        assert result.readings_count == 1

    def test_invalid_q10_raises(self):
        with pytest.raises(ValueError):
            Q10HerCalculator(q10_value=0)
        with pytest.raises(ValueError):
            Q10HerCalculator(q10_value=-1.5)

    def test_invalid_shelf_life_raises(self):
        with pytest.raises(ValueError):
            Q10HerCalculator(shelf_life_hours=0)

    def test_duplicate_timestamps_ignored(self):
        """قراءتان في نفس اللحظة يجب تجاهلهما."""
        t = datetime(2025, 1, 1)
        readings = [
            TemperatureReading(vaccine_id="V", value=30.0, recorded_at=t, duration_hours=1.0),
            TemperatureReading(vaccine_id="V", value=35.0, recorded_at=t, duration_hours=1.0),
        ]
        calc = Q10HerCalculator()
        result = calc.calculate(readings)
        assert result.cumulative_degradation_hours == 0.0


# ---------------------------------------------------------------------------
# scientific correctness
# ---------------------------------------------------------------------------

class TestQ10HerCalculatorScience:

    def test_at_reference_temp_no_degradation_acceleration(self):
        """
        عند درجة الحرارة المرجعية، عامل التسريع = 1.0.
        إذا أمضى اللقاح ساعة عند 5°C → 1 ساعة انحلال.
        """
        calc = Q10HerCalculator(
            q10_value=2.0,
            reference_temp=5.0,
            shelf_life_hours=720.0,
        )
        readings = make_readings([5.0, 5.0], interval_hours=1.0)
        result = calc.calculate(readings)

        expected_degradation = 1.0  # ساعة واحدة
        assert abs(result.cumulative_degradation_hours - expected_degradation) < 1e-9

    def test_above_reference_temp_accelerated_degradation(self):
        """
        عند 15°C (10 درجات فوق المرجع 5°C):
        عامل التسريع = 2^1 = 2.0
        ساعة عند 15°C = ساعتان انحلال مكافئ.
        """
        calc = Q10HerCalculator(
            q10_value=2.0,
            reference_temp=5.0,
            shelf_life_hours=720.0,
        )
        readings = make_readings([15.0, 15.0], interval_hours=1.0)
        result = calc.calculate(readings)

        expected_degradation = 2.0  # ساعتان
        assert abs(result.cumulative_degradation_hours - expected_degradation) < 1e-9

    def test_below_reference_temp_decelerated_degradation(self):
        """
        عند أقل من المرجع، عامل التسريع < 1.0 (التدهور يتباطأ).
        هذا يتوافق مع نموذج Q10 العلمي.
        """
        calc = Q10HerCalculator(
            q10_value=2.0,
            reference_temp=5.0,
            shelf_life_hours=720.0,
        )
        readings = make_readings([2.0, 2.0], interval_hours=1.0)
        result = calc.calculate(readings)
        
        # الحساب العلمي الصحيح:
        # exponent = (2.0 - 5.0) / 10.0 = -0.3
        # factor = 2.0 ** (-0.3) = 0.812252396
        expected_factor = 2.0 ** ((2.0 - 5.0) / 10.0)
        expected_degradation = expected_factor * 1.0  # ساعة واحدة
        
        assert abs(result.cumulative_degradation_hours - expected_degradation) < 1e-9
        # قيمة رقمية للتحقق السريع
        assert abs(result.cumulative_degradation_hours - 0.812252396) < 1e-6

    def test_is_critical_when_ratio_exceeds_one(self):
        """
        HER ratio > 1.0 يعني تجاوز العمر الافتراضي.
        """
        calc = Q10HerCalculator(
            q10_value=2.0,
            reference_temp=5.0,
            shelf_life_hours=0.5,  # نصف ساعة فقط
        )
        # ساعة عند 5°C = 1.0 ساعة انحلال → 1.0/0.5 = 2.0 ratio
        readings = make_readings([5.0, 5.0], interval_hours=1.0)
        result = calc.calculate(readings)

        assert result.her_ratio == pytest.approx(2.0, rel=1e-6)
        assert result.is_critical

    def test_percentage_consumed_property(self):
        calc = Q10HerCalculator(shelf_life_hours=100.0)
        readings = make_readings([5.0, 5.0], interval_hours=1.0)
        result = calc.calculate(readings)
        # her_ratio = 1/100 = 0.01 → percentage = 1.0%
        assert result.percentage_consumed == pytest.approx(1.0, rel=1e-6)

    def test_unsorted_readings_same_result(self):
        """ترتيب القراءات لا يجب أن يؤثر على النتيجة."""
        calc = Q10HerCalculator()
        t0 = datetime(2025, 6, 1)
        readings_sorted = [
            TemperatureReading("V", 8.0, t0, duration_hours=1.0),
            TemperatureReading("V", 12.0, t0 + timedelta(hours=1), duration_hours=1.0),
            TemperatureReading("V", 10.0, t0 + timedelta(hours=2), duration_hours=1.0),
        ]
        readings_shuffled = [readings_sorted[2], readings_sorted[0], readings_sorted[1]]

        result_sorted = calc.calculate(readings_sorted)
        result_shuffled = calc.calculate(readings_shuffled)

        assert abs(result_sorted.her_ratio - result_shuffled.her_ratio) < 1e-9

    def test_metadata_preserved(self):
        calc = Q10HerCalculator(q10_value=3.0, reference_temp=4.0)
        readings = make_readings([4.0, 4.0])
        result = calc.calculate(readings)

        assert result.q10_value_used == 3.0
        assert result.reference_temp_used == 4.0
        assert result.readings_count == 2


# ---------------------------------------------------------------------------
# independence from CCM
# ---------------------------------------------------------------------------

class TestHerCcmIndependence:

    def test_her_does_not_import_ccm(self):
        """التحقق من أن Q10HerCalculator لا يستورد شيئاً من CCM."""
        import importlib
        import sys

        mod_name = "src.domain.calculators.q10_her_calculator"
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
        else:
            mod = importlib.import_module(mod_name)

        source_file = mod.__file__
        with open(source_file) as f:
            content = f.read().lower()

        assert "ccm_calculator" not in content
        assert "ccmresult" not in content