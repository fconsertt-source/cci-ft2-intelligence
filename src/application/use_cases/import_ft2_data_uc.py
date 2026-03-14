from __future__ import annotations

from pathlib import Path
from typing import List

from src.application.ports.ft2_reader_port import Ft2ReaderPort
from src.application.ports.ft2_writer_port import Ft2WriterPort
from src.application.ports.logger_port import LoggerPort
from src.application.services.device_center_mapper import (  # ← الإضافة الوحيدة
    DeviceCenterMapper,
)
from src.domain.dtos.ft2_entry_dto import FT2EntryDTO


class ImportFt2DataUseCase:
    """Pure Use Case for importing FT2 raw data into intermediate JSON format.

    Responsibilities:
      - Orchestrate reading via Ft2ReaderPort
      - Orchestrate writing via Ft2WriterPort
      - Log progress (optional)
      - Enrich with administrative context (optional, via DeviceCenterMapper)

    Boundaries:
      - NO dependency on presentation layer
      - NO business logic (decision rules belong in evaluate_cold_chain)
      - NO infrastructure knowledge (adapters wired via DI container)
      - Enrichment is OPTIONAL — raw data path always preserved
    """

    def __init__(
        self,
        reader: Ft2ReaderPort,
        writer: Ft2WriterPort,
        logger: LoggerPort | None = None,
        mapper: DeviceCenterMapper | None = None,  # ← اختياري — لا يكسر التوافق الرجعي
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._logger = logger
        self._mapper = mapper  # ← None = no enrichment (system works without mapping)

    def execute(self, input_dir: Path, output_path: Path) -> None:
        if self._logger:
            self._logger.info(
                f"Importing FT2 data from '{input_dir}' to '{output_path}'"
            )

        try:
            # 1. Read all data from source directory (raw physical reality)
            ft2_data = self._reader.read(str(input_dir))
            if self._logger:
                self._logger.info(f"Read {len(ft2_data)} entries from source.")

            # 2. OPTIONAL: Enrich with administrative context (does NOT modify raw data)
            if self._mapper:
                enriched_data = self._enrich_with_center_context(ft2_data)
                ft2_data = enriched_data
                if self._logger:
                    mapped = sum(1 for e in ft2_data if e.center_id != "UNKNOWN")
                    self._logger.info(
                        f"Enriched {mapped}/{len(ft2_data)} entries with center context."
                    )

            # 3. Write the (optionally enriched) data to destination
            self._writer.write(ft2_data, output_path)
            if self._logger:
                self._logger.info("Successfully wrote data to destination.")

        except Exception as e:
            if self._logger:
                self._logger.error(f"An error occurred during data import: {e}")
            raise

    def _enrich_with_center_context(
        self, entries: List[FT2EntryDTO]
    ) -> List[FT2EntryDTO]:
        """Creates enriched copies WITHOUT modifying raw entries.

        Why copy instead of mutate?
          ✅ Preserves raw data path for forensic analysis
          ✅ Allows parallel Device-only and Center-enriched reports
          ✅ Immutable DTOs remain immutable (frozen=True)
        """
        enriched = []
        for entry in entries:
            context = (
                self._mapper.get_center_context(entry.device_id)
                if self._mapper
                else None
            )
            if (
                context
                and context.get("center_id")
                and context["center_id"] != "UNKNOWN"
            ):
                # Create enriched copy — raw entry remains untouched
                enriched_entry = FT2EntryDTO(
                    id=entry.id,
                    device_id=entry.device_id,
                    timestamp=entry.timestamp,
                    temperature=entry.temperature,
                    vaccine_type=entry.vaccine_type,
                    batch=entry.batch,
                    duration_minutes=entry.duration_minutes,
                    batch_id=entry.batch_id,
                    center_id=context["center_id"],  # ← Only enrichment
                )
                enriched.append(enriched_entry)
            else:
                enriched.append(entry)  # ← Raw data preserved as-is
        return enriched
