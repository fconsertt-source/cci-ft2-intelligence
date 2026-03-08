# src/application/dtos/ft2_entry_dto.py
"""Thin alias pointing at the canonical DTO defined in the domain layer.

The domain package is considered the source of truth for data shapes; the
application layer used to duplicate the definition here, leading to
maintenance drift.  We keep this module for import compatibility during the
migration, but it simply re-exports the domain class.
"""

from src.domain.dtos.ft2_entry_dto import FT2EntryDTO  # noqa: F401

__all__ = ["FT2EntryDTO"]
