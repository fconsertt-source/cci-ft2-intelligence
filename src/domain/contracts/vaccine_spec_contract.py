# src/domain/contracts/vaccine_spec_contract.py

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.vaccine_specification import VaccineSpecification


@dataclass(frozen=True)
class VaccineSpecContract:
    """
    Unified semantic contract over VaccineSpecification
    بدون تغيير الـ domain model الأساسي
    """

    spec: VaccineSpecification

    # ─────────────────────────────
    # SAFETY LAYER (critical decisions)
    # ─────────────────────────────

    def get_critical_temp(self) -> float:
        return self.spec.critical_temp_c

    def get_reference_temp(self) -> float:
        return self.spec.reference_temp_c

    def get_operational_max_temp(self) -> float:
        """
        IMPORTANT:
        max_temp is NOT legacy.
        It is operational boundary used across rules + degradation systems
        """
        return self.spec.max_temp

    # ─────────────────────────────
    # FREEZE LAYER
    # ─────────────────────────────

    def is_freeze_sensitive(self) -> bool:
        return self.spec.freeze_sensitive

    def get_freeze_threshold(self) -> float:
        return self.spec.freeze_threshold_c

    def get_freeze_range(self):
        return self.spec.freeze_range

    # ─────────────────────────────
    # VALIDATION LAYER
    # ─────────────────────────────

    def validate_internal_consistency(self) -> None:
        """
        Ensures no contradiction between layers
        """

        if self.spec.max_temp < self.spec.reference_temp_c:
            raise ValueError("Invalid thermal config: max_temp < reference_temp")

        if self.spec.critical_temp_c < self.spec.max_temp:
            raise ValueError("Inconsistent thresholds: critical < max_temp")
