"""Domain facade package.

This package provides a stable import surface for domain concepts by re-exporting
the existing domain-like modules under `src/core/` so callers can import from
`src.domain` as required by the new structure without immediately moving files.
"""
from src.core import entities as entities
from src.core import value_objects as value_objects
from src.core import services as services
from src.core import calculators as calculators
from src.core import enums as enums

__all__ = [
    "entities",
    "value_objects",
    "services",
    "calculators",
    "enums",
]
