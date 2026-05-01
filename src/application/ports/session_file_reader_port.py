from pathlib import Path
from typing import Any, Dict, Iterable, Protocol


class SessionFileReaderPort(Protocol):
    def read_rows(self, csv_path: Path) -> Iterable[Dict[str, Any]]:
        """Read a normalized session file as dictionaries."""
        ...
