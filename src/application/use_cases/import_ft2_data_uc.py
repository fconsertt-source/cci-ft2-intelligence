# src/application/use_cases/import_ft2_data_uc.py
from __future__ import annotations

from pathlib import Path

from src.application.ports.ft2_reader_port import Ft2ReaderPort
from src.application.ports.ft2_writer_port import Ft2WriterPort
from src.application.ports.logger_port import LoggerPort


class ImportFt2DataUseCase:
    """Pure Use Case for importing FT2 raw data into intermediate JSON format.
    
    Responsibilities:
      - Orchestrate reading via Ft2ReaderPort
      - Orchestrate writing via Ft2WriterPort
      - Log progress (optional)
    
    Boundaries:
      - NO dependency on presentation layer (guard.py removed)
      - NO business logic (decision rules belong in evaluate_cold_chain)
      - NO infrastructure knowledge (adapters wired via DI container)
    """
    
    def __init__(
        self,
        reader: Ft2ReaderPort,
        writer: Ft2WriterPort,
        logger: LoggerPort | None = None,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._logger = logger

    def execute(self, input_dir: Path, output_path: Path) -> None:
        if self._logger:
            self._logger.info(f"Importing FT2 data from '{input_dir}' to '{output_path}'")

        try:
            # 1. Read all data from source directory
            ft2_data = self._reader.read(input_dir)
            if self._logger:
                self._logger.info(f"Read {len(ft2_data)} entries from source.")

            # 2. Write the combined data to the destination file
            self._writer.write(output_path, ft2_data)
            if self._logger:
                self._logger.info("Successfully wrote data to destination.")

        except Exception as e:
            if self._logger:
                self._logger.error(f"An error occurred during data import: {e}")
            raise