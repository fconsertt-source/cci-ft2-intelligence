import csv
from pathlib import Path
from typing import Any, Dict, Iterable

from src.application.ports.session_file_reader_port import SessionFileReaderPort


class CsvSessionFileReader(SessionFileReaderPort):
    """Read FT2 session CSV/TSV files into plain dictionaries."""

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
