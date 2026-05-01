from typing import Any, Dict, Iterable, Iterator, List, Optional, Protocol


class SessionStoragePort(Protocol):
    def write_session(
        self,
        session_id: str,
        readings: Iterator[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist session rows and return the written location."""
        ...

    def read_session(
        self,
        session_id: str,
        columns: Optional[List[str]] = None,
        batch_size: int = 5_000,
    ) -> Iterable[Dict[str, Any]]:
        """Read session rows as dictionaries."""
        ...

    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Return metadata for a session, or an empty dict when missing."""
        ...
