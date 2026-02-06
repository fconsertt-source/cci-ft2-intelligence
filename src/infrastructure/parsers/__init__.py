"""Infrastructure parsers facade.

Re-exports concrete parser implementations that perform IO and parsing.
These modules are part of the Infrastructure layer per the Engineering Charter.
"""
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser

__all__ = ["FT2Parser"]
