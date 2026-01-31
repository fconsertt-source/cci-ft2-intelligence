from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from application.ports.logger_port import LoggerPort
from application.ports.report_generator_port import ReportGeneratorPort


@dataclass(frozen=True)
class GenerateReportRequest:
    data: object
    destination: Path


@dataclass(frozen=True)
class GenerateReportResponse:
    artifact: Path


class GenerateReportUseCase:
    def __init__(self, generator: ReportGeneratorPort, logger: LoggerPort | None = None) -> None:
        self._generator = generator
        self._logger = logger

    def execute(self, request: GenerateReportRequest) -> GenerateReportResponse:
        if self._logger:
            self._logger.info(f"Generating report to {request.destination}")
        artifact = self._generator.generate(request.data, request.destination)
        if self._logger:
            self._logger.debug(f"Report generated at {artifact}")
        return GenerateReportResponse(artifact=artifact)
