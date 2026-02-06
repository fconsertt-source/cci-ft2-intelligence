# src/application/ports/logger_port.py
from __future__ import annotations
from typing import Protocol


class LoggerPort(Protocol):
    """Minimal logger required by BaseUseCase."""
    def info(self, msg: str, *args, **kwargs) -> None: ...
    def debug(self, msg: str, *args, **kwargs) -> None: ...


class NoOpLogger:
    """Fallback logger that silently discards all messages."""
    def info(self, msg: str, *args, **kwargs) -> None:  # pragma: no cover
        pass

    def debug(self, msg: str, *args, **kwargs) -> None:  # pragma: no cover
        pass
