# src/core/calculators/vvm_q10_model.py

import math
from typing import List, Tuple

class VVMQ10Model:
    """
    A scientific utility to model vaccine shelf-life degradation using the
    Q10 temperature coefficient. This model calculates an acceleration factor
    for heat exposure based on the principles of the Arrhenius equation.

    It is designed as a non-decisional library to quantify heat impact,
    not to issue ACCEPT/REJECT verdicts.
    """

    def __init__(self, q10_value: float, ideal_temp: float):
        """
        Initializes the VVM Q10 Model with vaccine-specific parameters.

        Args:
        Initializes the model with specific vaccine characteristics.
        
        Args:
            q10_value: Typically 2.0 or higher depending on vaccine sensitivity.
            ideal_temp: Reference ideal storage temperature (e.g., 5.0°C).
        """
        if not isinstance(q10_value, (int, float)) or q10_value <= 0:
            raise ValueError("Q10 value must be a positive number.")
        if not isinstance(ideal_temp, (int, float)):
            raise ValueError("Ideal temperature must be a number.")

        self.q10_value = q10_value
        self.ideal_temp = ideal_temp

    def calculate_acceleration_factor(self, actual_temp: float) -> float:
        """

        Args:
            actual_temp (float): The actual temperature reading (°C).

        Returns:
            float: The calculated acceleration factor.
        """
        if not isinstance(actual_temp, (int, float)):
            raise ValueError("Actual temperature must be a number.")

        if actual_temp <= self.ideal_temp:
            return 1.0

        temp_diff = actual_temp - self.ideal_temp
        exponent = temp_diff / 10.0
        
        try:
            factor = math.pow(self.q10_value, exponent)
        except (ValueError, OverflowError):
            # Handles cases like math domain error if base is negative,
            # or overflow if the result is too large.
            return float('inf')

        if math.isnan(factor) or math.isinf(factor):
            # Defensive check against NaN or Inf results.
            # An infinite factor means extreme and immediate degradation.
            return float('inf')

        return factor

    def calculate_cumulative_degradation_hours(
        self,
        readings: List[Tuple[float, float]]
    ) -> float:
        """
        Calculates the total cumulative degradation, expressed in equivalent
        ideal hours, over a series of time-stamped temperature readings.

        Each segment's duration is multiplied by its calculated acceleration
        factor, and the results are summed.

        Args:
            readings (List[Tuple[float, float]]): A list of tuples, where
                each tuple contains (temperature_in_celsius, duration_in_hours).

        Returns:
            float: The total equivalent hours of shelf life consumed at the
                   ideal temperature.
        """
        total_degradation_hours = 0.0

        if not isinstance(readings, list):
            raise ValueError("Readings must be a list of (temp, duration) tuples.")

        for reading in readings:
            if not isinstance(reading, tuple) or len(reading) != 2:
                raise ValueError("Each reading must be a (temp, duration) tuple.")
            
            temp, duration_hours = reading
            
            if not isinstance(duration_hours, (int, float)) or duration_hours < 0:
                raise ValueError("Duration must be a non-negative number.")

            # Per spec, freeze conditions are handled elsewhere and bypass this model.
            # We assume inputs to this function have been pre-filtered.
            
            acceleration_factor = self.calculate_acceleration_factor(temp)
            
            degradation_for_segment = duration_hours * acceleration_factor
            total_degradation_hours += degradation_for_segment

        return total_degradation_hours
