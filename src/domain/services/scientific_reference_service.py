from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.domain.engines.reference_exposure_engine import ReferenceExposureEngine
from src.domain.value_objects.reference_engine_result import ReferenceEngineResult
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.value_objects.vaccine_specification import VaccineSpecification, get_vaccine_spec
from src.infrastructure.repositories.yaml_vaccine_spec_repository import YamlVaccineSpecRepository


class ScientificReferenceService:
    """
    Audit-only service for parallel scientific reference analysis.
    """

    def __init__(self, library_path: Path = Path("config/vaccine_library.yaml")) -> None:
        self._repository = YamlVaccineSpecRepository(library_path=library_path)
        self._engine = ReferenceExposureEngine()
        self._constants = self._load_constants()

    def _load_constants(self) -> Dict[str, Any]:
        path = Path("config/scientific_constants.yaml")
        if not path.exists():
            return {
                "ea_kj_mol": 83.144,
                "reference_temp_c": 5.0,
                "gas_constant_j_mol_k": 8.314,
            }
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("scientific_constants", {})

    def analyze(
        self,
        entries: List[TemperatureEntry],
        vaccine_type: Optional[str] = None,
        supply_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        vaccine_key = (vaccine_type or "GENERAL").upper().strip()
        spec = self._repository.get_spec(vaccine_key)
        if spec is None:
            spec = get_vaccine_spec(vaccine_key)

        if not entries:
            return {
                "reference_audit_enabled": True,
                "reference_her_ratio": 0.0,
                "reference_mkt_c": spec.reference_temp_c,
                "reference_source": spec.regulatory_source or "WHO/IVB/06.10",
                "reference_rationale": spec.rationale,
                "reference_traceability": {
                    "source_file": "config/vaccine_library.yaml",
                    "engine": "reference_audit",
                    "model": "Arrhenius + MKT",
                    "verified": "false",
                },
            }

        result = self._engine.analyze(entries, spec)
        return {
            "reference_audit_enabled": True,
            "reference_her_ratio": result.her_ratio,
            "reference_mkt_c": result.mkt_c,
            "reference_ea_kj_mol": result.ea_kj_mol,
            "reference_temp_c": result.reference_temp_c,
            "reference_shelf_life_days": result.shelf_life_days,
            "reference_source": result.source,
            "reference_rationale": result.rationale,
            "reference_traceability": result.traceability,
        }
