# src/application/use_cases/generate_report_uc.py
from __future__ import annotations
from src.application.ports.report_generator_port import ReportGeneratorPort

class GenerateReportUseCase:
    def __init__(self, generator: ReportGeneratorPort):
        self._generator = generator

    def execute(self, input_path: str, output_path: str) -> str:
        return self._generator.generate(input_path, output_path)