import pytest
from src.core.calculators.vvm_q10_model import VVMQ10Model

# --- Constants for testing ---
Q10_VALUE = 2.0
IDEAL_TEMP = 5.0

@pytest.fixture
def model():
    """Provides a default VVMQ10Model instance for tests."""
    return VVMQ10Model(q10_value=Q10_VALUE, ideal_temp=IDEAL_TEMP)

class TestVVMQ10ModelInitialization:
    def test_valid_initialization(self):
        """Tests successful model instantiation."""
        model = VVMQ10Model(q10_value=2.0, ideal_temp=5.0)
        assert model.q10_value == 2.0
        assert model.ideal_temp == 5.0

    @pytest.mark.parametrize("invalid_q10", [0, -1, "abc", None])
    def test_invalid_q10_value_raises_error(self, invalid_q10):
        """Tests that invalid Q10 values raise a ValueError."""
        with pytest.raises(ValueError, match="Q10 value must be a positive number."):
            VVMQ10Model(q10_value=invalid_q10, ideal_temp=IDEAL_TEMP)

    @pytest.mark.parametrize("invalid_temp", ["abc", None])
    def test_invalid_ideal_temp_raises_error(self, invalid_temp):
        """Tests that invalid ideal temperatures raise a ValueError."""
        with pytest.raises(ValueError, match="Ideal temperature must be a number."):
            VVMQ10Model(q10_value=Q10_VALUE, ideal_temp=invalid_temp)

class TestAccelerationFactorCalculation:
    """Tests the calculate_acceleration_factor method."""

    def test_protocol_zero_effect_at_ideal_temp(self, model):
        """Acceptance Test: T_actual == T_ideal yields 1.0."""
        assert model.calculate_acceleration_factor(IDEAL_TEMP) == 1.0

    def test_protocol_zero_effect_below_ideal_temp(self, model):
        """Acceptance Test: T_actual < T_ideal yields 1.0."""
        assert model.calculate_acceleration_factor(IDEAL_TEMP - 5) == 1.0
        assert model.calculate_acceleration_factor(0) == 1.0

    def test_calculation_above_ideal(self, model):
        """Tests a standard calculation where T_actual > T_ideal."""
        # T_actual = 10, T_ideal = 5. Diff = 5. Exp = 0.5. Factor = 2^0.5
        expected_factor = 2.0**0.5
        assert model.calculate_acceleration_factor(10.0) == pytest.approx(expected_factor)

    def test_protocol_linear_step_test(self, model):
        """Acceptance Test: +10°C increase multiplies factor by exact Q10 value."""
        # At 15°C, diff is 10, exponent is 1, factor should be Q10_VALUE
        temp1 = IDEAL_TEMP + 10
        factor1 = model.calculate_acceleration_factor(temp1)
        assert factor1 == pytest.approx(Q10_VALUE)

        # At 25°C, diff is 20, exponent is 2, factor should be Q10_VALUE^2
        temp2 = IDEAL_TEMP + 20
        factor2 = model.calculate_acceleration_factor(temp2)
        assert factor2 == pytest.approx(Q10_VALUE**2)
        
        # Check the multiplicative effect
        assert factor2 / factor1 == pytest.approx(Q10_VALUE)

    @pytest.mark.parametrize("invalid_temp", ["abc", None])
    def test_invalid_actual_temp_raises_error(self, model, invalid_temp):
        """Tests that non-numeric actual_temp raises a ValueError."""
        with pytest.raises(ValueError, match="Actual temperature must be a number."):
            model.calculate_acceleration_factor(invalid_temp)

class TestCumulativeDegradation:
    """Tests the calculate_cumulative_degradation_hours method."""

    def test_protocol_accumulation_test_simple(self, model):
        """Acceptance Test: Correct handling of fragmented time segments."""
        # Segment 1: 2 hours at 15°C (10°C above ideal). Factor = 2. Degradation = 2*2 = 4 hours.
        # Segment 2: 3 hours at 5°C (at ideal). Factor = 1. Degradation = 3*1 = 3 hours.
        # Segment 3: 1 hour at 25°C (20°C above ideal). Factor = 4. Degradation = 1*4 = 4 hours.
        readings = [
            (15.0, 2.0),  # T+10
            (5.0, 3.0),   # T_ideal
            (25.0, 1.0),  # T+20
        ]
        
        # Total expected degradation: (2.0 * 2) + (3.0 * 1) + (1.0 * 4) = 4 + 3 + 4 = 11
        expected_degradation = (2.0 * model.calculate_acceleration_factor(15.0)) + \
                               (3.0 * model.calculate_acceleration_factor(5.0)) + \
                               (1.0 * model.calculate_acceleration_factor(25.0))

        assert expected_degradation == pytest.approx(11.0)
        
        total_degradation = model.calculate_cumulative_degradation_hours(readings)
        assert total_degradation == pytest.approx(expected_degradation)

    def test_accumulation_with_all_segments_below_ideal(self, model):
        """Tests accumulation where all temps are at or below ideal."""
        readings = [
            (5.0, 10.0), # At ideal
            (2.0, 5.0),  # Below ideal
            (0.0, 2.0)   # Below ideal
        ]
        # Factor is 1.0 for all. Total degradation should just be total duration.
        total_duration = 10.0 + 5.0 + 2.0
        assert model.calculate_cumulative_degradation_hours(readings) == pytest.approx(total_duration)

    def test_empty_readings_list(self, model):
        """Tests that an empty list of readings results in zero degradation."""
        assert model.calculate_cumulative_degradation_hours([]) == 0.0

    @pytest.mark.parametrize("invalid_reading", [
        "not a list",
        [(10, 1), "not a tuple"],
        [(10, 1, 1)], # wrong tuple size
        [(10, "abc")], # invalid duration
        [(10, -1)],   # negative duration
    ])
    def test_invalid_readings_format_raises_error(self, model, invalid_reading):
        with pytest.raises(ValueError):
            model.calculate_cumulative_degradation_hours(invalid_reading)

    def test_extreme_temperature_overflow(self, model):
        """Tests handling of extreme temperatures that cause math overflow."""
        # 11000°C with Q10=2 will definitely trigger OverflowError in math.pow
        factor = model.calculate_acceleration_factor(11000.0)
        assert factor == float('inf')

    def test_calculate_acceleration_factor_nan_inf_check(self, model):
        """Manually check that the model handles non-finite results if math.pow didn't raise."""
        # This is hard to trigger with valid inputs, but we want to ensure coverage
        # by checking a very large temperature that might return inf without raising.
        factor = model.calculate_acceleration_factor(20000.0)
        assert factor == float('inf')
