from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from src.domain.ports.vaccine_specification_port import VaccineSpecificationPort
from src.domain.value_objects.vaccine_specification import VaccineSpecification, get_vaccine_spec
from src.infrastructure.utils.error_translator import translate_infrastructure_errors
from src.infrastructure.utils.vaccine_library_loader import load_vaccine_library


class YamlVaccineSpecRepository(VaccineSpecificationPort):
    """
    Additive YAML-backed vaccine specification repository.

    Intended as a safe SSOT reader for the parallel reference path.
    It does not replace legacy catalogue usage; it only exposes YAML data
    in a form compatible with the existing VaccineSpecification contract.
    """

    @translate_infrastructure_errors
    def __init__(self, library_path: Path = Path("config/vaccine_library.yaml")):
        self._library_path = library_path
        self._library = load_vaccine_library(str(library_path))

    def get_library_metadata(self) -> dict[str, Any]:
        return dict(self._library.get("metadata", {}))

    def get_defaults(self) -> dict[str, Any]:
        return dict(self._library.get("defaults", {}))

    def _get_required_float(
        self,
        spec_data: dict[str, Any],
        defaults: dict[str, Any],
        key: str,
        vaccine_name: str,
    ) -> float:
        value = spec_data.get(key)
        if value is None:
            value = defaults.get(key)

        if value is None:
            raise ValueError(
                f"Missing required vaccine specification field '{key}' for {vaccine_name}"
            )

        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid numeric value for '{key}' in vaccine {vaccine_name}: {value}"
            ) from exc

    def get_vaccine_spec(self, vaccine_type: str) -> Optional[VaccineSpecification]:
        normalized = (vaccine_type or "GENERAL").upper().strip()
        vaccines = self._library.get("vaccines", {})
        spec_data = vaccines.get(normalized)

        if not spec_data:
            return get_vaccine_spec(normalized)

        defaults = self.get_defaults()

        return VaccineSpecification(
            vaccine_type=normalized,
            q10_factor=float(spec_data.get("q10_factor", defaults.get("q10_factor", 2.0))),
            shelf_life_days=float(spec_data.get("shelf_life_days", defaults.get("shelf_life_days", 730.0))),
            reference_temp_c=float(spec_data.get("reference_temp_c", defaults.get("reference_temp_c", 5.0))),
            activation_energy_kj_mol=self._get_required_float(
                spec_data,
                defaults,
                "activation_energy_kj_mol",
                normalized,
            ),
            degradation_days_at_37C=self._get_required_float(
                spec_data,
                defaults,
                "degradation_days_at_37C",
                normalized,
            ),
            freeze_sensitive=bool(spec_data.get("freeze_sensitive", defaults.get("freeze_sensitive", False))),
            vvm_type=spec_data.get("vvm_type"),
            critical_temp_c=float(spec_data.get("critical_temp_c", defaults.get("critical_temp_c", 34.0))),
            critical_hours=float(spec_data.get("critical_hours", defaults.get("critical_hours", 2.0))),
            rationale=spec_data.get("note", spec_data.get("source", "")),
            min_temp=float(defaults.get("reference_temp_c", 2.0)),
            max_temp=8.0,
            excursion_time_limit=spec_data.get("excursion_time_limit"),
            freeze_range=None,
            max_heat_temp=spec_data.get("critical_temp_c", defaults.get("critical_temp_c", 34.0)),
            max_heat_duration_hours=spec_data.get("critical_hours", defaults.get("critical_hours", 2.0)),
            regulatory_source=spec_data.get("source"),
        )

    def get_spec(self, vaccine_type: str) -> Optional[VaccineSpecification]:
        return self.get_vaccine_spec(vaccine_type)