import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.application.ports.session_file_reader_port import SessionFileReaderPort
from src.application.ports.session_registry_port import SessionRegistryPort
from src.application.ports.session_storage_port import SessionStoragePort


class _StdlibCsvSessionFileReader(SessionFileReaderPort):
    """Backward-compatible default reader for callers that do not inject one."""

    def read_rows(self, csv_path: Path) -> Iterable[Dict[str, Any]]:
        with Path(csv_path).open("r", newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t") if sample else csv.excel
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)
            for row in reader:
                yield dict(row)


def _timestamp_key(row: Dict[str, Any]) -> str:
    return str(row.get("timestamp", ""))


def _sort_and_deduplicate(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduplicated: Dict[str, Dict[str, Any]] = {}
    for row in sorted(rows, key=_timestamp_key):
        deduplicated[_timestamp_key(row)] = row
    return list(deduplicated.values())


class IncrementalPipelineProcessor:
    """Safe incremental processing without DataFrame or infrastructure coupling."""

    def __init__(
        self,
        registry: SessionRegistryPort,
        storage: SessionStoragePort,
        file_reader: Optional[SessionFileReaderPort] = None,
    ):
        self.registry = registry
        self.storage = storage
        self.file_reader = file_reader or _StdlibCsvSessionFileReader()

    def extract_metadata(self, csv_path: Path) -> dict:
        """استخراج device_id من اسم الملف"""
        stem = csv_path.stem
        match = re.match(r"^(\d+)", stem)
        if not match:
            raise ValueError(f"Invalid FT2 filename format: {csv_path.name}")

        device_id = match.group(1)

        ts_match = re.search(r"_(\d{8}\d{4})", stem)
        if ts_match:
            ts_str = ts_match.group(1)
            report_dt = datetime.strptime(ts_str, "%Y%m%d%H%M")
        else:
            report_dt = datetime.fromtimestamp(csv_path.stat().st_mtime)

        return {
            "device_id": device_id,
            "report_timestamp": report_dt,
            "filename": csv_path.name,
            "full_path": str(csv_path),
        }

    def process_file(self, csv_path: Path, force: bool = False) -> dict:
        """معالجة ملف FT2 بشكل تزايدي"""
        meta = self.extract_metadata(csv_path)
        device_id = meta["device_id"]
        file_ts = meta["report_timestamp"]

        if not force and not self.registry.is_new_data(device_id, file_ts):
            return {"status": "skipped", "reason": "already_processed", **meta}

        new_rows = _sort_and_deduplicate(self.file_reader.read_rows(csv_path))
        existing_rows: List[Dict[str, Any]] = []
        if self.storage.get_session_metadata(device_id):
            existing_rows = list(self.storage.read_session(device_id))

        merged = _sort_and_deduplicate([*existing_rows, *new_rows])

        self.storage.write_session(device_id, iter(merged))
        self.registry.mark_processed(device_id, file_ts, csv_path.name, len(new_rows))

        timestamps = [_timestamp_key(row) for row in merged]
        time_range = (min(timestamps), max(timestamps)) if timestamps else (None, None)

        return {
            "status": "processed",
            "device_id": device_id,
            "new_readings": len(new_rows),
            "total_readings": len(merged),
            "time_range": time_range,
        }
