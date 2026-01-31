from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from application.dtos.analysis_result_dto import AnalysisResultDTO
from application.ports.ft2_reader_port import Ft2ReaderPort
from application.ports.logger_port import LoggerPort


@dataclass(frozen=True)
class ImportFt2DataRequest:
    source: Path


@dataclass(frozen=True)
class ImportFt2DataResponse:
    result: AnalysisResultDTO


class ImportFt2DataUseCase:
    def __init__(self, reader: Ft2ReaderPort, logger: LoggerPort | None = None) -> None:
        self._reader = reader
        self._logger = logger

    def execute(self, request: ImportFt2DataRequest) -> ImportFt2DataResponse:
        if self._logger:
            self._logger.info(f"Importing FT2 data from {request.source}")
        result = self._reader.read(request.source)
        if self._logger:
            self._logger.debug("FT2 data imported and mapped to DTO")
        return ImportFt2DataResponse(result=result)
