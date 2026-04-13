from __future__ import annotations

from typing import Any, Mapping, Protocol


class BaseDTO(Protocol):
    """All DTOs must implement a deterministic dict representation."""

    def to_dict(self) -> Mapping[str, Any]: ...
