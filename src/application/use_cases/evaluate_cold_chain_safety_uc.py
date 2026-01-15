from typing import List
from src.core.calculators.ccm_calculator import CCMCalculator
from src.core.engines.heat_exposure_engine import HeatExposureEngine
from src.core.entities.temperature_reading import TemperatureReading
from src.application.dtos.analysis_result_dto import (
    AnalysisResultDTO,
    VaccineStatus,
)


class EvaluateColdChainSafetyUC:
    """
    Use Case الرسمي لتقييم سلامة سلسلة التبريد
    """

    def __init__(self, reader, repository=None):
        self.reader = reader
        self.repository = repository
        self.ccm_calculator = CCMCalculator()

    def execute(self) -> List[AnalysisResultDTO]:
        vaccines = self.reader.get_vaccines()
        readings = self.reader.read_all()

        results: List[AnalysisResultDTO] = []

        for vaccine in vaccines:
            v_readings = [r for r in readings if r.vaccine_id == vaccine.id]

            if not v_readings:
                continue

            ccm = self.ccm_calculator.calculate(v_readings)

            engine = HeatExposureEngine(vaccine.reference_table)
            exposure_minutes = self._estimate_exposure_minutes(v_readings)
            avg_temp = sum(r.value for r in v_readings) / len(v_readings)
            her = engine.compute_her(avg_temp, exposure_minutes)

            status = self._determine_status(ccm, her)

            results.append(
                AnalysisResultDTO(
                    vaccine_id=vaccine.id,
                    status=status,
                    her=her,
                    ccm=ccm,
                )
            )

        if self.repository:
            self.repository.save_all(results)

        return results

    def _estimate_exposure_minutes(self, readings: List[TemperatureReading]) -> int:
        if len(readings) == 1:
            return 60
        start = readings[0].recorded_at
        end = readings[-1].recorded_at
        return int((end - start).total_seconds() / 60)

    def _determine_status(self, ccm: float, her: float) -> VaccineStatus:
        if her >= 1.0:
            return VaccineStatus.DISCARD
        if her > 0.5 or ccm > 20:
            return VaccineStatus.PARTIAL
        return VaccineStatus.SAFE
