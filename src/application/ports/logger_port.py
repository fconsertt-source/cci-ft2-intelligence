from __future__ import annotations

from typing import Protocol


class LoggerPort(Protocol):
    """Optional logging abstraction for application layer."""

    def info(self, msg: str) -> None: ...

    def warning(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...

    def debug(self, msg: str) -> None: ...
