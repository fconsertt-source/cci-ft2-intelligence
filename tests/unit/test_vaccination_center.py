# tests/unit/test_vaccination_center.py
import pytest
from datetime import datetime
from src.domain.entities.vaccination_center import VaccinationCenter, FreezeTolerance
from src.ft2_reader.parser.ft2_parser import FT2Entry

@pytest.fixture
def zero_tolerance_center():
    """Provides a center with zero tolerance for freezing."""
    return VaccinationCenter(
        id="center_zt",
        name="Zero Tolerance Center",
        device_ids=["device_zt1"],
        temperature_ranges={"min": 2, "max": 8},
        decision_thresholds={},
        freeze_tolerance=FreezeTolerance.ZERO_TOLERANCE,
    )

def test_initial_decision_is_no_data(zero_tolerance_center):
    """Tests that the initial decision state of a center is 'NO_DATA'."""
    assert zero_tolerance_center.decision == "NO_DATA"

def test_add_normal_entry_does_not_change_decision(zero_tolerance_center):
    """
    Tests that adding an entry with a normal temperature does not trigger a
    rejection decision.
    """
    # Arrange
    normal_entry = FT2Entry("device_zt1", datetime.now(), 5.0, "Vax", "B1")
    
    # Act
    zero_tolerance_center.add_ft2_entry(normal_entry)

    # Assert
    # The internal decision logic _update_decision is basic and might not
    # transition to an "OK" state, but it should not reject.
    assert zero_tolerance_center.decision != "REJECTED_FREEZE_SENSITIVE"
    assert len(zero_tolerance_center.ft2_entries) == 1

def test_add_freeze_entry_to_zero_tolerance_center_rejects_stock(zero_tolerance_center):
    """
    Tests that adding a single freeze event entry to a ZERO_TOLERANCE center
    immediately changes the decision to 'REJECTED_FREEZE_SENSITIVE'.
    """
    # Arrange
    freeze_entry = FT2Entry("device_zt1", datetime.now(), -1.0, "Vax", "B2")

    # Act
    zero_tolerance_center.add_ft2_entry(freeze_entry)

    # Assert
    assert zero_tolerance_center.decision == "REJECTED_FREEZE_SENSITIVE"
    assert zero_tolerance_center.vvm_stage == "D"
    assert len(zero_tolerance_center.ft2_entries) == 1

def test_count_freeze_events_correctly_counts_and_groups(zero_tolerance_center):
    """
    Tests the internal _count_freeze_events method for accuracy.
    """
    # Arrange
    entries = [
        FT2Entry("device_zt1", datetime.now(), -0.6, "Vax", "B1", duration_minutes=10),
        FT2Entry("device_zt1", datetime.now(), 2.0, "Vax", "B2"),
        FT2Entry("device_zt1", datetime.now(), -5.0, "Vax", "B3", duration_minutes=20),
        # Add another device to the center to test grouping
        FT2Entry("device_zt2", datetime.now(), -2.0, "Vax", "B4", duration_minutes=15),
    ]
    zero_tolerance_center.device_ids.append("device_zt2")
    zero_tolerance_center.ft2_entries.extend(entries)

    # Act
    freeze_stats = zero_tolerance_center._count_freeze_events()

    # Assert
    assert freeze_stats["total"] == 3
    assert sorted(freeze_stats["durations"]) == [10, 15, 20]
    assert freeze_stats["by_device"]["device_zt1"] == 2
    assert freeze_stats["by_device"]["device_zt2"] == 1

def test_add_boundary_temp_entry_does_not_reject(zero_tolerance_center):
    """
    Tests that a temperature of exactly -0.5 is not considered a freeze event.
    The condition is temp < -0.5.
    """
    # Arrange
    boundary_entry = FT2Entry("device_zt1", datetime.now(), -0.5, "Vax", "B5")

    # Act
    zero_tolerance_center.add_ft2_entry(boundary_entry)

    # Assert
    assert zero_tolerance_center.decision != "REJECTED_FREEZE_SENSITIVE"
