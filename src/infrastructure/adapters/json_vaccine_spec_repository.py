from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.domain.ports.vaccine_specification_port import \
    VaccineSpecificationPort
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class JsonVaccineSpecRepository(VaccineSpecificationPort):
    """
    JSON-based implementation of VaccineSpecificationPort.
    Reads vaccine specifications from a JSON file.
    """

    def __init__(self, spec_file: Path = Path("data/vaccine_specs.json")):
        self._spec_file = spec_file
        self._specs = self._load_specs()

    def _load_specs(self) -> dict[str, VaccineSpecification]:
        """Load vaccine specifications from JSON file."""
        if not self._spec_file.exists():
            return self._get_default_specs()

        try:
            with open(self._spec_file, 'r') as f:
                data = json.load(f)

            specs = {}
            for vaccine_type, spec_data in data.items():
                specs[vaccine_type] = VaccineSpecification(
                    vaccine_type=vaccine_type,
                    min_temp=spec_data["min_temp"],
                    max_temp=spec_data["max_temp"],
                    freeze_sensitive=spec_data["freeze_sensitive"],
                    rationale=spec_data.get("rationale", ""),
                    freeze_range=spec_data.get("freeze_range"),
                    max_heat_temp=spec_data.get("max_heat_temp"),
                    max_heat_duration_hours=spec_data.get("max_heat_duration_hours"),
                    regulatory_source=spec_data.get(
                        "regulatory_source", "WHO/IVB/06.10"
                    ),
                    excursion_time_limit=spec_data.get(
                        "excursion_time_limit"
                    ),  # ← الحقل الجديد
                    activation_energy_kj_mol=float(spec_data.get("activation_energy_kj_mol", 83.144)),
                    degradation_days_at_37C=float(spec_data.get("degradation_days_at_37C", 14.0)),
                )
            return specs
        except Exception:
            return self._get_default_specs()

    def _get_default_specs(self) -> dict[str, VaccineSpecification]:
        """Return default vaccine specifications."""
        return {
            "Hepatitis_B": VaccineSpecification(
                vaccine_type="Hepatitis_B",
                min_temp=2.0,
                max_temp=8.0,
                freeze_sensitive=True,
                rationale="Standard Hepatitis B storage requirements",
                freeze_range=None,
                max_heat_temp=37.0,
                max_heat_duration_hours=72.0,
                regulatory_source="WHO/IVB/06.10",
                excursion_time_limit=72.0,  # ← الحقل الجديد
                activation_energy_kj_mol=83.144,
                degradation_days_at_37C=7.0,
            ),
            "General": VaccineSpecification(
                vaccine_type="General",
                min_temp=2.0,
                max_temp=8.0,
                freeze_sensitive=False,
                rationale="General vaccine storage requirements",
                freeze_range=None,
                max_heat_temp=37.0,
                max_heat_duration_hours=24.0,
                regulatory_source="WHO/IVB/06.10",
                excursion_time_limit=24.0,  # ← الحقل الجديد
                activation_energy_kj_mol=83.144,
                degradation_days_at_37C=14.0,
            ),
        }

    def get_spec(self, vaccine_type: str) -> Optional[VaccineSpecification]:
        """Get thermal specification for a vaccine type."""
        return self._specs.get(vaccine_type)
