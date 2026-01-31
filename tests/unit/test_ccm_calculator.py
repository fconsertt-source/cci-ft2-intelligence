import pytest
from datetime import datetime, timedelta
from src.domain.calculators.ccm_calculator import CCMCalculator
from src.domain.entities.temperature_reading import TemperatureReading

class TestCCMCalculator:
    
    @pytest.fixture
    def calculator(self):
        return CCMCalculator(threshold=1.0, method="both")

    def test_calculate_delta_no_readings(self, calculator):
        assert calculator.calculate_delta([]) == 0.0

    def test_calculate_delta_single_reading(self, calculator):
        reading = TemperatureReading("v1", 5.0, datetime.now())
        assert calculator.calculate_delta([reading]) == 0.0

    def test_calculate_delta_below_threshold(self, calculator):
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 5.0, t0),
            TemperatureReading("v1", 5.5, t0 + timedelta(minutes=10)), # Delta 0.5 < 1.0
            TemperatureReading("v1", 5.0, t0 + timedelta(minutes=20)), # Delta 0.5 < 1.0
        ]
        assert calculator.calculate_delta(readings) == 0.0

    def test_calculate_delta_accumulates(self, calculator):
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 5.0, t0),
            TemperatureReading("v1", 7.0, t0 + timedelta(minutes=10)), # Delta 2.0
            TemperatureReading("v1", 4.0, t0 + timedelta(minutes=20)), # Delta 3.0
        ]
        # Total = 2.0 + 3.0 = 5.0
        assert calculator.calculate_delta(readings) == 5.0

    def test_calculate_auc_simple(self, calculator):
        # Base temp is 8.0 by default in calculate_auc
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 10.0, t0),
            TemperatureReading("v1", 10.0, t0 + timedelta(minutes=60)),
        ]
        # Temp 10.0 is 2.0 above 8.0.
        # Duration 60 mins.
        # AUC = 2.0 * 60 = 120.0
        assert calculator.calculate_auc(readings) == 120.0

    def test_calculate_auc_varying(self, calculator):
        # Trapezoid validation
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 8.0, t0), # Excess 0
            TemperatureReading("v1", 10.0, t0 + timedelta(minutes=60)), # Excess 2
        ]
        # Avg excess = (0 + 2) / 2 = 1.0
        # Duration = 60
        # AUC = 60.0
        assert calculator.calculate_auc(readings) == 60.0

    def test_calculate_auc_below_base(self, calculator):
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 5.0, t0),
            TemperatureReading("v1", 6.0, t0 + timedelta(minutes=60)),
        ]
        # Both below 8.0, AUC should be 0
        assert calculator.calculate_auc(readings) == 0.0

    def test_calculate_full(self, calculator):
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 5.0, t0),
            TemperatureReading("v1", 10.0, t0 + timedelta(minutes=60)),
        ]
        result = calculator.calculate(readings)
        assert "ccm_delta" in result
        assert "ccm_auc" in result
        assert result["method_used"] == "both"
