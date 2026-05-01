from __future__ import annotations

from typing import Any, Protocol


class ValidationPort(Protocol):
    """
    Contract for a validator that can perform:
    * Structural validation (pydantic, value‑objects, regex, …)
    * Business‑rule validation (Domain policies)
    """

    def validate(self, obj: Any) -> None:  # pragma: no cover
        """Raise ``ValidationError`` if ``obj`` is not valid."""
        ...
