# tests/unit/domain/test_device_identity.py
"""Unit tests for DeviceIdentity entity."""

import pytest

from src.domain.entities.device_identity import DeviceIdentity


def test_device_identity_str_and_validation():
    di = DeviceIdentity(device_id="FT2-001", serial_number="SN12345")
    assert str(di) == "FT2-001 (SN12345)"
    assert di.device_id == "FT2-001"
    assert di.serial_number == "SN12345"
    # center is optional
    di2 = di.with_center("C-10")
    assert di2.center_id == "C-10"


def test_device_identity_empty_fields_raises():
    with pytest.raises(ValueError):
        DeviceIdentity(device_id="", serial_number="SN")
    with pytest.raises(ValueError):
        DeviceIdentity(device_id="ID", serial_number="   ")
