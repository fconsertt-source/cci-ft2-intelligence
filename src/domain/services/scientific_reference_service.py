from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.engines.reference_exposure_engine import ReferenceExposureEngine
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.value_objects.vaccine_specification import get_vaccine_spec
from src.domain.ports.vaccine_specification_port import VaccineSpecificationPort


class ScientificReferenceService:
    """
    Audit-only service for parallel scientific reference analysis.
    """

    def __init__(
        self,
        spec_port: Optional[VaccineSpecificationPort] = None,
        constants: Optional[Dict[str, Any]] = None,
        library_path=None,
    ) -> None:
        self._spec_port = spec_port
        self._constants = constants or self._default_constants()
        self._engine = ReferenceExposureEngine(
            ea_kj_mol=float(self._constants.get("ea_kj_mol", 83.144)),
            reference_temp_c=float(self._constants.get("reference_temp_c", 37.0)),
        )

    def _default_constants(self) -> Dict[str, Any]:
        return {
            "ea_kj_mol": 83.144,
            "reference_temp_c": 37.0,
            "gas_constant_j_mol_k": 8.314,
        }

    def analyze(
        self,
        entries: List[TemperatureEntry],
        vaccine_type: Optional[str] = None,
        supply_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        vaccine_key = (vaccine_type or "GENERAL").upper().strip()
        spec = None
        if self._spec_port is not None:
            spec = self._spec_port.get_spec(vaccine_key)
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
