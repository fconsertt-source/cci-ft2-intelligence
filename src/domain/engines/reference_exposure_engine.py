from __future__ import annotations

from typing import Iterable

from src.domain.calculators.arrhenius_her_calculator import ArrheniusHERCalculator
from src.domain.calculators.mkt_calculator import MKTCalculator
from src.domain.value_objects.reference_engine_result import ReferenceEngineResult
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.value_objects.vaccine_specification import VaccineSpecification


class ReferenceExposureEngine:
    """
    Parallel reference exposure engine implementing the scientific audit path.
    """

    def __init__(self, ea_kj_mol: float = 83.144) -> None:
        self._her_calculator = ArrheniusHERCalculator(ea_kj_mol=ea_kj_mol)
        self._mkt_calculator = MKTCalculator(ea_kj_mol=ea_kj_mol)

    def analyze(
        self,
        entries: Iterable[TemperatureEntry],
        spec: VaccineSpecification,
    ) -> ReferenceEngineResult:
        her_result = self._her_calculator.calculate(entries, spec.shelf_life_hours)
        mkt_c = self._mkt_calculator.calculate(entries)

        return ReferenceEngineResult(
            vaccine_type=spec.vaccine_type,
            her_ratio=her_result.her_ratio,
            mkt_c=mkt_c,
            ea_kj_mol=self._her_calculator.ea_j_mol / 1000.0,
            reference_temp_c=spec.reference_temp_c,
            shelf_life_days=spec.shelf_life_days,
            rationale=spec.rationale,
            source=spec.regulatory_source or "WHO/IVB/06.10",
            traceability={
                "source_file": "config/vaccine_library.yaml",
                "engine": "ArrheniusReferenceExposureEngine",
                "model": "Arrhenius + MKT",
                "verified": "true",
            },
        )
