"""
Contract tests for time-related constants used in the service layer.
"""

import pytest


def test_time_unit_constant():
    """Ensure the CCMCalculator exposes a TIME_UNIT constant set to minutes."""
    from src.domain.calculators.ccm_calculator import TIME_UNIT

    assert (
        TIME_UNIT == "minutes"
    ), "TIME_UNIT must be 'minutes' for all AUC/delta computations"
