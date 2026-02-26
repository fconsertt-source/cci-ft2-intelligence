from __future__ import annotations

from typing import List, Dict

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class ThermalDegradationEstimator:
    """
    Provides SCIENTIFIC ESTIMATES only.
    NEVER influences decision path.
    Pure domain service - no port needed.
    """
    
    def estimate_remaining_potency(
        self, 
        thermal_history: List[ThermalRecord], 
        spec: VaccineSpecification
    ) -> float:
        """
        Returns: estimated remaining potency percentage (0.0 - 100.0)
        For ADVISORY purposes only.
        """
        # ← Q10 model calculation
        # ← Cumulative damage calculation
        # ← No return of "DISCARD"/"SAFE" - only numerical estimate
        
        # Simplified Q10 calculation
        total_damage = 0.0
        for record in thermal_history:
            if record.temperature > spec.max_temp:
                # Calculate heat damage using Q10 factor
                delta_t = record.temperature - spec.max_temp
                time_hours = record.duration_minutes / 60
                # Simplified Q10: damage doubles every 10°C above threshold
                q10_factor = 2.0  # Typical for biological products
                damage = (delta_t / 10.0) * time_hours * q10_factor
                total_damage += damage
            elif record.temperature <= 0.0 and spec.freeze_sensitive:
                # Absolute freeze damage for sensitive vaccines
                total_damage += 100.0  # Maximum damage
        
        # Convert damage to remaining potency (100 - damage)
        remaining_potency = max(0.0, 100.0 - total_damage)
        return remaining_potency
    
    def calculate_cumulative_impact(
        self, 
        thermal_history: List[ThermalRecord], 
        spec: VaccineSpecification
    ) -> Dict:
        """
        Returns: detailed cumulative impact analysis
        For ADVISORY purposes only.
        """
        freeze_events = 0
        heat_events = 0
        total_heat_hours = 0.0
        max_temp_exceeded_count = 0
        
        for record in thermal_history:
            # التصحيح: فقط إذا كان اللقاح حساسًا للتجميد
            if spec.freeze_sensitive and record.temperature <= 0.0:
                freeze_events += 1
            elif record.temperature > spec.max_temp:
                heat_events += 1
                total_heat_hours += record.duration_minutes / 60
            # التصحيح: التحقق من None بشكل آمن
            max_heat_temp = spec.max_heat_temp if spec.max_heat_temp is not None else spec.max_temp
            if record.temperature > max_heat_temp:
                max_temp_exceeded_count += 1
        
        return {
            "freeze_events": freeze_events,
            "heat_events": heat_events,
            "total_heat_hours": total_heat_hours,
            "max_temp_exceeded_count": max_temp_exceeded_count,
            "remaining_potency_estimate": self.estimate_remaining_potency(thermal_history, spec)
        }
