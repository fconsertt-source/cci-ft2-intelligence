from __future__ import annotations

from src.domain.value_objects.vaccine_specification import VaccineSpecification


class RegulatoryDecisionService:
    """
    Makes decisions based on REGULATORY THRESHOLDS ONLY.
    No probabilistic models allowed in decision path.
    """
    
    def evaluate(
        self, 
        temperature: float, 
        duration_minutes: float, 
        spec: VaccineSpecification
    ) -> str:  # Returns "SAFE", "PARTIAL", or "DISCARD"
        """
        Returns: Decision based on REGULATORY SOURCES only.
        """
        # Critical: Freeze check - absolute rule for freeze-sensitive vaccines
        if spec.freeze_sensitive and temperature <= 0.0:
            return "DISCARD"  # ← No probability, no estimation, absolute rule
        
        # Critical: Freeze check - for freeze-stable vaccines in wrong temperature
        if not spec.freeze_sensitive:
            # Check if in frozen range for freeze-stable (should be SAFE)
            if spec.freeze_range:
                freeze_min, freeze_max = spec.freeze_range
                if freeze_min <= temperature <= freeze_max:
                    return "SAFE"  # ← Frozen storage allowed for freeze-stable
                # Check if freeze-stable vaccine got unintended freeze (outside range)
                elif temperature <= 0.0:  # ← If not in range and <= 0
                    return "DISCARD"  # ← Unexpected freeze for freeze-stable
            # If no freeze_range defined but temperature <= 0
            elif temperature <= 0.0:
                return "DISCARD"  # ← Unexpected freeze for freeze-stable
        
        # Heat check - regulatory threshold
        if temperature > spec.max_temp:
            duration_hours = duration_minutes / 60
            max_allowed_hours = spec.max_heat_duration_hours or 0
            
            if duration_hours >= max_allowed_hours:
                return "DISCARD"  # ← Based on WHO regulation
        
        # Heat check - max temperature exceeded
        max_heat_temp = spec.max_heat_temp if spec.max_heat_temp is not None else spec.max_temp
        if temperature > max_heat_temp:
            return "DISCARD"  # ← Exceeded maximum allowed temperature
        
        # Within range - safe
        return "SAFE"  # ← Binary outcome based on regulatory thresholds
