import pytest

from src.infrastructure.parsers import FT2Parser
from src.infrastructure.validators import FT2Validator
from src.shared.di_container import create_evaluate_cold_chain_uc


class DummyReader:
    def get_vaccines(self):
        return []

    def read_all(self):
        return []


def test_reexports_importable():
    # Ensure that re-exports are importable and callable
    assert hasattr(FT2Parser, 'parse_file')
    assert hasattr(FT2Validator, 'validate_temporal_consistency') or hasattr(FT2Validator, 'validate')


def test_uc_creation_and_execute_returns_list():
    reader = DummyReader()
    uc = create_evaluate_cold_chain_uc(reader=reader)
    results = uc.execute()
    assert isinstance(results, list)
