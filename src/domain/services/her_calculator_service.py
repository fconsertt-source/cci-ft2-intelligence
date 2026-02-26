# src/domain/services/her_calculator_service.py
class HerCalculatorService(Protocol):
    """Separate strategy for HER calculation — maintains dual integration."""
    def calculate(self, readings: List[TemperatureReading]) -> HERResult:
        ...

class CcmCalculatorService(Protocol):
    """Separate strategy for CCM calculation — maintains dual integration."""
    def calculate(self, readings: List[TemperatureReading]) -> CCMResult:
        ...

# src/domain/calculators/q10_her_calculator.py
class Q10HerCalculator(HerCalculatorService):
    """Advanced Q10 model — still independent from CCM."""
    def calculate(self, readings: List[TemperatureReading]) -> HERResult:
        # ← HER فقط — لا تؤثر على CCM
        pass

# src/domain/calculators/time_weighted_ccm_calculator.py
class TimeWeightedCcmCalculator(CcmCalculatorService):
    """Advanced time-weighted model — still independent from HER."""
    def calculate(self, readings: List[TemperatureReading]) -> CCMResult:
        # ← CCM فقط — لا تؤثر على HER
        pass