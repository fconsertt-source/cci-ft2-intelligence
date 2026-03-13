# tests/unit/domain/calculators/test_ccm_calculator.py

from datetime import datetime

import pytest

from src.domain.calculators.ccm_calculator import CCMCalculator, calculate_delta_minutes

# helper utilities moved to shared time_factory to avoid duplication across tests
from tests.helpers.time_factory import create_reading, minutes


def test_calculate_delta_minutes_helper():
    """Helper should return minute difference, not seconds."""
    from datetime import datetime

    rec = {
        "previous_timestamp": datetime(2025, 1, 1, 0, 0, 0),
        "timestamp": datetime(2025, 1, 1, 1, 0, 0),
    }
    assert calculate_delta_minutes(rec) == 60.0


class TestCCMCalculator:
    """Unit tests for CCMCalculator."""

    def test_calculate_delta_empty_list(self):
        """Delta with no readings returns 0."""
        calc = CCMCalculator()
        assert calc.calculate_delta([]) == 0.0

    def test_calculate_delta_single_reading(self):
        """Delta with one reading returns 0."""
        readings = [create_reading(5.0, minutes(0))]
        calc = CCMCalculator()
        assert calc.calculate_delta(readings) == 0.0

    def test_calculate_delta_no_exceed_threshold(self):
        """Delta changes below threshold are ignored."""
        readings = [
            create_reading(5.0, 0),
            create_reading(5.5, 60),  # Δ = 0.5 < 1.0
            create_reading(5.8, 120),  # Δ = 0.3 < 1.0
        ]
        calc = CCMCalculator(threshold=1.0)
        assert calc.calculate_delta(readings) == 0.0

    def test_calculate_delta_with_exceeds(self):
        """Delta changes above threshold are summed."""
        readings = [
            create_reading(5.0, 0),
            create_reading(6.5, 60),  # Δ = 1.5 ≥ 1.0
            create_reading(5.0, 120),  # Δ = 1.5 ≥ 1.0
            create_reading(5.1, 180),  # Δ = 0.1 < 1.0
        ]
        calc = CCMCalculator(threshold=1.0)
        # expected: 1.5 + 1.5 = 3.0
        assert calc.calculate_delta(readings) == 3.0

    def test_calculate_delta_custom_threshold(self):
        """Respect custom threshold."""
        readings = [
            create_reading(5.0, 0),
            create_reading(6.0, 60),  # Δ = 1.0 (equal)
            create_reading(7.0, 120),  # Δ = 1.0 (equal)
        ]
        calc = CCMCalculator(threshold=1.0)
        # both deltas are exactly 1.0, so both count
        assert calc.calculate_delta(readings) == 2.0

        calc2 = CCMCalculator(threshold=1.5)
        # none exceed 1.5
        assert calc2.calculate_delta(readings) == 0.0

    def test_calculate_auc_empty(self):
        """AUC with no readings returns 0."""
        calc = CCMCalculator()
        assert calc.calculate_auc([]) == 0.0

    def test_calculate_auc_single_reading(self):
        """AUC with one reading returns 0."""
        readings = [create_reading(10.0, minutes(0))]
        calc = CCMCalculator()
        assert calc.calculate_auc(readings) == 0.0

    def test_calculate_auc_no_exceed_base(self):
        """AUC when all temps below base returns 0."""
        readings = [
            create_reading(5.0, 0),
            create_reading(6.0, 60),
            create_reading(7.0, 120),
        ]
        calc = CCMCalculator()
        # base_temp default = 8.0, all below
        assert calc.calculate_auc(readings) == 0.0

    def test_calculate_auc_with_excess(self):
        """AUC computed correctly for trapezoids."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(5.0, 0, base),  # below base
            create_reading(9.0, 60, base),  # 1° above base
            create_reading(10.0, 120, base),  # 2° above base
        ]
        calc = CCMCalculator()
        # compute expected using actual time differences (in minutes)
        dt1 = (readings[1].recorded_at - readings[0].recorded_at).total_seconds() / 60
        avg_exc1 = (max(0, 5.0 - 8.0) + max(0, 9.0 - 8.0)) / 2
        auc1 = avg_exc1 * dt1
        dt2 = (readings[2].recorded_at - readings[1].recorded_at).total_seconds() / 60
        avg_exc2 = (max(0, 9.0 - 8.0) + max(0, 10.0 - 8.0)) / 2
        auc2 = avg_exc2 * dt2
        expected = auc1 + auc2
        assert calc.calculate_auc(readings) == expected

    def test_calculate_auc_with_mixed(self):
        """AUC handles intervals where only one endpoint exceeds base."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(7.0, 0, base),  # below base (8)
            create_reading(9.0, 60, base),  # above base
        ]
        calc = CCMCalculator()
        # compute using actual delta_minutes
        dt = (readings[1].recorded_at - readings[0].recorded_at).total_seconds() / 60
        avg_exc = (max(0, 7.0 - 8.0) + max(0, 9.0 - 8.0)) / 2
        assert calc.calculate_auc(readings) == avg_exc * dt

    def test_calculate_auc_large_time_gap(self):
        """AUC scales with time difference."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(10.0, 0, base),  # excess 2
            create_reading(10.0, 120, base),  # excess 2, dt=120min
        ]
        calc = CCMCalculator()
        # avg_excess = 2, dt=120 -> 240
        assert calc.calculate_auc(readings) == 240.0

    def test_calculate_method_returns_dict(self):
        """Calculate returns a dictionary with both metrics."""
        readings = [
            create_reading(5.0, 0),
            create_reading(6.5, 60),  # Δ=1.5
            create_reading(5.0, 120),  # Δ=1.5
        ]
        calc = CCMCalculator(method="both")
        result = calc.calculate(readings)
        assert isinstance(result, dict)
        assert "ccm_delta" in result
        assert "ccm_auc" in result
        assert "method_used" in result
        assert result["ccm_delta"] == 3.0
        # AUC: first interval: excess: 0 and (6.5-8? negative) => 0, second interval: excess: 0 and 0? actually 6.5 <8 so excess 0, 5.0<8, so AUC=0
        assert result["ccm_auc"] == 0.0
        assert result["method_used"] == "both"

    def test_calculate_with_custom_base_temp(self):
        """AUC respects custom base_temp."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(7.0, 0, base),
            create_reading(7.5, 60, base),
        ]
        calc = CCMCalculator()
        # with base_temp=8.0, both below => AUC=0
        assert calc.calculate_auc(readings) == 0.0
        # with base_temp=7.0, now above base
        assert calc.calculate_auc(readings, base_temp=7.0) == pytest.approx(
            0.25 * 60
        )  # avg_excess=0.25, dt=60

    def test_calculate_delta_with_unsorted_readings(self):
        """Calculator sorts readings by time."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(10.0, 120, base),  # later
            create_reading(5.0, 0, base),  # earlier
        ]
        calc = CCMCalculator(threshold=1.0)
        # after sorting: 5.0 then 10.0, delta=5.0 >=1.0
        assert calc.calculate_delta(readings) == 5.0

    def test_calculate_auc_with_unsorted_readings(self):
        """AUC sorts readings by time."""
        base = datetime(2025, 1, 1, 0, 0, 0)
        readings = [
            create_reading(10.0, 120, base),  # later
            create_reading(5.0, 0, base),  # earlier
        ]
        calc = CCMCalculator()
        # sorted: 5.0 then 10.0; interval: excess: 0 and 2, avg=1, dt=120min => 120
        assert calc.calculate_auc(readings) == 120.0
