# src/application/use_cases/generate_vaccines_report_uc.py
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.application.services.vaccines_report_generator import VaccinesReportGenerator
from src.domain.value_objects.vaccine_assessment_result import VaccineAssessmentResult
from src.domain.enums.vaccine_decision import VaccineDecision


@dataclass
class GenerateVaccinesReportRequest:
    assessments: List[VaccineAssessmentResult]
    output_path: Path


@dataclass
class GenerateVaccinesReportResponse:
    report_path: Path
    total_count: int
    safe_count: int
    partial_count: int
    discard_count: int
    expired_count: int


class GenerateVaccinesReportUseCase:
    def __init__(self, report_generator: VaccinesReportGenerator):
        self.report_generator = report_generator

    def execute(self, request: GenerateVaccinesReportRequest) -> GenerateVaccinesReportResponse:
        report_path = self.report_generator.generate(
            assessments=request.assessments,
            output_path=request.output_path,
        )

        safe = sum(1 for a in request.assessments if a.decision == VaccineDecision.SAFE)
        partial = sum(1 for a in request.assessments if a.decision == VaccineDecision.PARTIAL)
        discard = sum(1 for a in request.assessments if a.decision == VaccineDecision.DISCARD)
        expired = sum(1 for a in request.assessments if a.decision == VaccineDecision.EXPIRED)

        return GenerateVaccinesReportResponse(
            report_path=report_path,
            total_count=len(request.assessments),
            safe_count=safe,
            partial_count=partial,
            discard_count=discard,
            expired_count=expired,
        )