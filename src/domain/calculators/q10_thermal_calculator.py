# src/domain/calculators/q10_thermal_calculator.py
from __future__ import annotations

from src.application.ports.thermal_impact_calculator_port import ThermalImpactCalculatorPort
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class Q10ThermalCalculator(ThermalImpactCalculatorPort):
    """
    Q10-based thermal impact calculator.
    Implements the thermal_impact_calculator_port interface.
    """

    def evaluate(
        self,
        temperature: float,
        duration_minutes: float,
        specification: VaccineSpecification
    ) -> str:  # Returns "SAFE", "PARTIAL", or "DISCARD"
        """
        Evaluate thermal impact based on temperature and duration.
        
        This is a simplified implementation. Real Q10 model would be more complex.
        """
        # Check if temperature is out of range
        if temperature < specification.min_temp or temperature > specification.max_temp:
            # Check if it's a freezing issue
            if specification.freeze_sensitive and temperature <= 0:
                return "DISCARD"
            
            # Check duration impact
            duration_hours = duration_minutes / 60
            
            if duration_hours > specification.excursion_time_limit:
                return "DISCARD"
            elif duration_hours > specification.excursion_time_limit / 2:
                return "PARTIAL"
            else:
                return "SAFE"
        else:
            # Within normal range
            return "SAFE"
