# tests/unit/test_ft2_linker.py
import pytest
from datetime import datetime
from src.infrastructure.adapters.ft2_reader.services.ft2_linker import FT2Linker
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Entry
from src.domain.entities.vaccination_center import VaccinationCenter, FreezeTolerance

# Fixtures for test data

@pytest.fixture
def sample_centers():
    """Provides a list of sample vaccination centers."""
    return [
        VaccinationCenter(
            id="center1",
            name="Center A",
            device_ids=["device_A1", "device_A2"],
            temperature_ranges={"min": 2, "max": 8},
            decision_thresholds={},
        ),
        VaccinationCenter(
            id="center2",
            name="Center B",
            device_ids=["device_B1"],
            temperature_ranges={"min": 2, "max": 8},
            decision_thresholds={},
        ),
    ]

@pytest.fixture
def sample_entries():
    """Provides a list of sample FT2 entries."""
    return [
        FT2Entry("device_A1", datetime.now(), 5.0, "VaxA", "Batch1"),
        FT2Entry("device_B1", datetime.now(), 4.0, "VaxB", "Batch2"),
        FT2Entry("device_A2", datetime.now(), -1.0, "VaxA", "Batch3"), # Freeze event
        FT2Entry("device_C1", datetime.now(), 6.0, "VaxC", "Batch4"), # Unknown device
    ]

# Test Cases

def test_link_method_assigns_entries_to_correct_centers(sample_entries, sample_centers):
    """
    Tests that the `link` static method correctly assigns entries to their
    corresponding vaccination centers based on device_id.
    """
    # Arrange
    center_a = sample_centers[0]
    center_b = sample_centers[1]

    # Act
    FT2Linker.link(sample_entries, sample_centers)

    # Assert
    assert len(center_a.ft2_entries) == 2
    assert len(center_b.ft2_entries) == 1
    
    # Check that the correct entries were added
    center_a_device_ids = {entry.device_id for entry in center_a.ft2_entries}
    assert "device_A1" in center_a_device_ids
    assert "device_A2" in center_a_device_ids
    
    center_b_device_ids = {entry.device_id for entry in center_b.ft2_entries}
    assert "device_B1" in center_b_device_ids

    # Check that the unknown entry was not added to any center
    assert all("device_C1" not in {e.device_id for e in center.ft2_entries} for center in sample_centers)

def test_link_generator_yields_correct_tuples(sample_entries, sample_centers):
    """
    Tests that the `link_generator` yields the correct (entry, center) tuples,
    including (entry, None) for unlinked entries.
    """
    # Arrange
    center_a = sample_centers[0]
    center_b = sample_centers[1]
    
    # Act
    linked_results = list(FT2Linker.link_generator(sample_entries, sample_centers))

    # Assert
    assert len(linked_results) == len(sample_entries) # Should yield a result for every entry

    # Expected mappings
    expected_map = {
        "device_A1": center_a,
        "device_B1": center_b,
        "device_A2": center_a,
        "device_C1": None,
    }

    for entry, center in linked_results:
        assert center == expected_map[entry.device_id]

def test_link_with_no_matching_centers(sample_centers):
    """
    Tests that no entries are linked when device IDs do not match any center.
    """
    # Arrange
    entries = [
        FT2Entry("device_X", datetime.now(), 5.0, "VaxX", "BatchX"),
        FT2Entry("device_Y", datetime.now(), 4.0, "VaxY", "BatchY"),
    ]
    
    # Act
    FT2Linker.link(entries, sample_centers)

    # Assert
    for center in sample_centers:
        assert len(center.ft2_entries) == 0

def test_link_with_empty_entries_list(sample_centers):
    """
    Tests that the function handles an empty list of entries gracefully.
    """
    # Arrange
    entries = []
    
    # Act
    FT2Linker.link(entries, sample_centers)

    # Assert
    for center in sample_centers:
        assert len(center.ft2_entries) == 0

def test_link_with_empty_centers_list(sample_entries):
    """
    Tests that the function handles an empty list of centers gracefully.
    """
    # Arrange
    centers = []
    
    # Act
    linked_results = list(FT2Linker.link_generator(sample_entries, centers))

    # Assert
    # All entries should be yielded with None as the center
    assert len(linked_results) == len(sample_entries)
    assert all(center is None for entry, center in linked_results)
