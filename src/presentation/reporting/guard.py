# src/reporting/guard.py
"""
Guard Layer – stream‑based reporting with immutable snapshot.

Features:
* Write DTOs incrementally (no temporary files).
* Errors are stored both in the snapshot and a dedicated JSON error file.
* Filenames contain timestamp + short UUID to avoid collisions.
* Temporary files are fully removed even if an exception occurs.
"""

from __future__ import annotations

import csv
import datetime
import json
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Mapping, Protocol, Set


# ----------------------------------------------------------------------
# Protocol – What the Use‑Case expects from a Guard writer
# ----------------------------------------------------------------------
class GuardWriter(Protocol):
    def add_dto(self, dto: Any) -> None: ...
    def track_file(self, path: Path) -> None: ...
    def record_error(self, error: Mapping[str, Any]) -> None: ...
    def finalize(self, start_ts: datetime.datetime) -> None: ...


# ----------------------------------------------------------------------
# Concrete implementation (stream‑based, no temporary JSON per DTO)
# ----------------------------------------------------------------------
class _GuardWriter:
    """Stream‑based Guard writer.

    All DTOs are kept in memory (list of dicts).  This is safe for the
    typical use‑case (< 10 k DTOs).  For truly massive batches you could
    switch back to temporary files.
    """

    def __init__(self, use_case: str, out_dir: Path):
        self.use_case = use_case

        # Ensure the base output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)

        # Final destination per use‑case
        self._final_dir = out_dir / use_case / "final"
        self._final_dir.mkdir(parents=True, exist_ok=True)

        # In‑memory buffers
        self._dtos: List[Mapping[str, Any]] = []
        self._errors: List[Mapping[str, Any]] = []
        self._tracked_files: Set[Path] = set()

    # ------------------------------------------------------------------
    # Public API (used by BaseUseCase)
    # ------------------------------------------------------------------
    def add_dto(self, dto: Any) -> None:
        """Append a DTO to the internal list."""
        data = dto.to_dict() if hasattr(dto, "to_dict") else dto
        self._dtos.append(data)

    def track_file(self, path: Path) -> None:
        self._tracked_files.add(path.resolve())

    def record_error(self, error: Mapping[str, Any]) -> None:
        """Store an error – will be written to a dedicated JSON file."""
        self._errors.append(error)

    # ------------------------------------------------------------------
    # Finalization – write JSON, CSV, Snapshot and error file
    # ------------------------------------------------------------------
    def finalize(self, start_ts: datetime.datetime) -> None:
        ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
        uid = uuid.uuid4().hex[:8]  # short unique suffix

        # -------------------- JSON file --------------------
        json_path = self._final_dir / f"{self.use_case}_{ts}_{uid}.json"
        json_path.write_text(
            json.dumps(self._dtos, ensure_ascii=False, sort_keys=True, indent=2)
        )

        # -------------------- CSV file --------------------
        if self._dtos:
            csv_path = self._final_dir / f"{self.use_case}_{ts}_{uid}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(self._dtos[0].keys()))
                writer.writeheader()
                writer.writerows(self._dtos)

        # -------------------- Snapshot (human readable) --------------------
        snap_path = self._final_dir / f"{self.use_case}_{ts}_{uid}.snap"
        with snap_path.open("w", encoding="utf-8") as f:
            f.write(f"# Guard Report – {self.use_case}\n")
            f.write(f"Start: {start_ts.isoformat()}\n")
            f.write(f"End:   {datetime.datetime.utcnow().isoformat()}\n")
            f.write("\nTracked files:\n")
            for p in sorted(self._tracked_files):
                f.write(f"  - {p}\n")
            f.write("\nDTOs:\n")
            for dto in self._dtos:
                f.write(json.dumps(dto, ensure_ascii=False, sort_keys=True, indent=2))
                f.write("\n---\n")
            if self._errors:
                f.write("\nErrors:\n")
                for err in self._errors:
                    f.write(
                        json.dumps(err, ensure_ascii=False, sort_keys=True, indent=2)
                    )
                    f.write("\n---\n")

        # -------------------- Separate error JSON (CI‑friendly) --------------------
        if self._errors:
            err_path = self._final_dir / f"{self.use_case}_errors_{uid}.json"
            err_path.write_text(
                json.dumps(self._errors, ensure_ascii=False, sort_keys=True, indent=2)
            )

        # No temporary directory to clean – everything lives in memory.
        # If you need to guarantee cleanup even when an exception occurs,
        # the contextmanager below guarantees `finalize` is always called.


# ----------------------------------------------------------------------
# Context manager used by BaseUseCase
# ----------------------------------------------------------------------
@contextmanager
def guard_scope(use_case: str, out_dir: Path = Path.cwd() / "reports"):
    """
    Open a Guard writer, yield it, and always finalize on exit.
    The writer is *stream‑based* – no temporary files are created.
    """
    writer = _GuardWriter(use_case, out_dir)
    start = datetime.datetime.utcnow()
    try:
        yield writer
    finally:
        writer.finalize(start)
