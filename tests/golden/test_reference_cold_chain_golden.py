"""Proposed golden tests for future parallel reference cold-chain coverage.

Discovery-only scaffold:
- documents intended fixture layout
- validates manifest/fixture consistency
- keeps current operational path untouched
"""

import json
from pathlib import Path

import pytest


BASE_DIR = Path("tests/golden/reference_cold_chain")
METADATA_FILE = BASE_DIR / "reference_golden_metadata.json"
FIXTURES_DIR = BASE_DIR / "fixtures"


def _load_metadata() -> dict:
    return json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def _load_fixture(name: str) -> dict:
    metadata = _load_metadata()
    fixture_path = BASE_DIR / metadata["fixtures"][name]["file"]
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_reference_cold_chain_fixture_schema_is_valid():
    metadata = _load_metadata()

    assert metadata["contract_notes"]["parallel_path_only"] is True
    assert metadata["contract_notes"]["direct_replacement_forbidden"] is True
    assert metadata["contract_notes"]["extra_stats_prefix"] == "reference_"

    for fixture_name, fixture_info in metadata["fixtures"].items():
        fixture_path = BASE_DIR / fixture_info["file"]
        assert fixture_path.exists(), f"Missing fixture for {fixture_name}: {fixture_path}"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "safe_nominal",
        "freeze_breach",
        "heat_duration_breach",
        "no_data",
        "borderline_freeze_threshold",
        "borderline_heat_duration_threshold",
        "mixed_excursion_freeze_and_heat",
        "vaccine_profile_sensitivity_compare",
    ],
)
def test_reference_cold_chain_fixture_contract_shape(fixture_name):
    fixture = _load_fixture(fixture_name)

    assert "scenario" in fixture
    assert "input" in fixture
    assert "expected_reference" in fixture
    assert "coverage_target" in fixture

    expected_reference = fixture["expected_reference"]
    assert "reference_extra_stats" in expected_reference

    for key in expected_reference["reference_extra_stats"]:
        assert key.startswith("reference_"), f"New additive metric must use reference_ prefix: {key}"


def test_reference_cold_chain_safe_nominal_matches_golden():
    fixture = _load_fixture("safe_nominal")
    assert fixture["expected_reference"]["reference_extra_stats"]["reference_has_freeze"] is False


def test_reference_cold_chain_freeze_breach_matches_golden():
    fixture = _load_fixture("freeze_breach")
    assert fixture["expected_reference"]["reference_extra_stats"]["reference_has_freeze"] is True


def test_reference_cold_chain_heat_duration_breach_matches_golden():
    fixture = _load_fixture("heat_duration_breach")
    assert fixture["expected_reference"]["reference_extra_stats"]["reference_has_heat_duration_breach"] is True


def test_reference_cold_chain_no_data_matches_golden():
    fixture = _load_fixture("no_data")
    assert fixture["input"]["readings"] == []
    assert fixture["expected_reference"]["reference_extra_stats"]["reference_no_data"] is True


def test_reference_cold_chain_parallel_path_preserves_primary_decision_contract():
    fixture = _load_fixture("safe_nominal")
    assert fixture["expected_reference"]["primary_path_preserved"] is True


def test_reference_cold_chain_extra_stats_only_uses_reference_namespace_for_new_metrics():
    for fixture_name in _load_metadata()["fixtures"]:
        fixture = _load_fixture(fixture_name)
        for key in fixture["expected_reference"]["reference_extra_stats"]:
            assert key.startswith("reference_")