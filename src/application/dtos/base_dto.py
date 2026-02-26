from __future__ import annotations
from typing import Protocol, Mapping, Any

class BaseDTO(Protocol):
    """All DTOs must implement a deterministic dict representation."""
    def to_dict(self) -> Mapping[str, Any]: ...
