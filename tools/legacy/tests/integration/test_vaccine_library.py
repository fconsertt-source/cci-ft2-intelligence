import pytest
from src.utils.vaccine_library_loader import VaccineLibrary

@pytest.fixture
def library():
    # Using the default config path for the test
    return VaccineLibrary()

def test_library_loads_data(library):
    assert len(library.vaccines) > 0
    assert "pfizer" in library.vaccines

def test_get_vaccine_by_name(library):
    vax = library.get_vaccine_by_name("pfizer")
    assert vax is not None
    assert vax.name.lower() == "pfizer"

def test_get_vaccine_not_found(library):
    vax = library.get_vaccine_by_name("non_existent_vax")
    assert vax is None