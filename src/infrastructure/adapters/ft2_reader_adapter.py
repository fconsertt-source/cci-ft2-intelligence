from typing import List
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.adapters.ft2_reader.validator.ft2_validator import FT2Validator


class FT2ReaderAdapter:
    """Adapter that exposes the reader interface expected by Use Cases.

    This adapter wraps the existing parser/validator implementations and
    provides `get_vaccines()` and `read_all()` methods used by Use Cases.
    """

    def __init__(self, input_dir: str = "data/input_ft2"):
        self.input_dir = input_dir

    def get_vaccines(self) -> List:
        # For now, Use Cases may depend on external vaccine list; return empty to be safe.
        return []

    def read_all(self) -> List:
        # Parse all files in input_dir using FT2Parser
        import os
        entries = []
        if not os.path.exists(self.input_dir):
            return entries

        for f in os.listdir(self.input_dir):
            if f.endswith(('.csv', '.tsv')):
                path = os.path.join(self.input_dir, f)
                entries.extend(FT2Parser.parse_file(path))

        # Optionally validate (FT2Validator has validate_temporal_consistency)
        return entries
