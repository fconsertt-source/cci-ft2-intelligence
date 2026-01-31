"""Infrastructure validators facade.

Re-exports concrete validators that inspect parsed data and perform IO-adjacent checks.
"""
from src.ft2_reader.validator.ft2_validator import FT2Validator

__all__ = ["FT2Validator"]
