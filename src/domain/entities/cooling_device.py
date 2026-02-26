from __future__ import annotations
from dataclasses import dataclass
from typing import List
from datetime import datetime
from src.domain.enums.vvm_stage import VVMStage


@dataclass(frozen=True)
class DeviceSafetyResult:
    """Result of individual device safety evaluation."""
    device_id: str
    status: str  # SAFE, PARTIAL, DISCARD, NO_DATA
    her: float
    ccm: float
    vvm_stage: VVMStage


@dataclass(frozen=True)
class CoolingDevice:
    """Physical cooling device (fridge/freezer) — NOT a logical grouping.
    
    Represents a single Berlinger Fridge-tag® 2 E device with its own thermal history.
    Metadata fields (location, capacity_liters) are descriptive ONLY — not used in safety calculations.
    """
    device_id: str
    location: str          # ← وصفي فقط — لا يدخل في حسابات السلامة
    vaccine_type: str
    capacity_liters: float # ← وصفي فقط — لا يدخل في حسابات السلامة
    
    def evaluate_safety(self, readings: List) -> DeviceSafetyResult:
        """Evaluate THIS device only — no aggregation."""
        if not readings:
            return DeviceSafetyResult(
                device_id=self.device_id,
                status="NO_DATA",
                her=0.0,
                ccm=0.0,
                vvm_stage=VVMStage.NONE
            )
        
        # Simplified HER calculation (real implementation uses dedicated calculators)
        avg_temp = sum(r.temperature for r in readings) / len(readings) if readings else 0.0
        her = avg_temp * len(readings) / 1440.0 if readings else 0.0
        
        # Decision logic
        if her < 10.0:
            status = "SAFE"
            vvm_stage = VVMStage.A
        elif her < 20.0:
            status = "PARTIAL"
            vvm_stage = VVMStage.B
        else:
            status = "DISCARD"
            vvm_stage = VVMStage.C
        
        return DeviceSafetyResult(
            device_id=self.device_id,
            status=status,
            her=her,
            ccm=her * 1.2,  # Simplified CCM
            vvm_stage=vvm_stage
        )
