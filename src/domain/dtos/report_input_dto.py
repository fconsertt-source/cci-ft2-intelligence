from __future__ import annotations

from dataclasses import asdict, dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .base_dto import BaseDTO


def make_immutable(obj: Any) -> Any:
    """Recursively convert lists to tuples and dicts to MappingProxyType."""
    if isinstance(obj, list):
        return tuple(make_immutable(x) for x in obj)
    if isinstance(obj, dict):
        return MappingProxyType({k: make_immutable(v) for k, v in obj.items()})
    return obj


@dataclass(frozen=True)
class ReportInputDTO(BaseDTO):
    center_id: str
    period_start: str
    period_end: str
    metrics: Tuple[float, ...] = field(default_factory=tuple)
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metrics", make_immutable(self.metrics))
        object.__setattr__(self, "meta", make_immutable(self.meta))

    def to_dict(self) -> dict:
        return asdict(self)
