from datetime import datetime, timedelta

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.validators.cold_chain_continuity import ColdChainContinuityValidator


class TestColdChainContinuityValidator:

    def test_validate_with_contiguous_records(self):
        records = [
            ThermalRecord(device_id="DEV1", timestamp=datetime(2025, 1, 1, 9, 0, 0), temperature=5.0, duration_minutes=15.0, vaccine_type="A"),
            ThermalRecord(device_id="DEV1", timestamp=datetime(2025, 1, 1, 10, 30, 0), temperature=5.5, duration_minutes=15.0, vaccine_type="A"),
        ]

        result = ColdChainContinuityValidator.validate(records, device_id="DEV1")

        assert result.valid is True
        assert result.warning is None
        assert result.gaps == []

    def test_validate_detects_critical_gap(self):
        records = [
            ThermalRecord(device_id="DEV2", timestamp=datetime(2025, 1, 1, 9, 0, 0), temperature=4.0, duration_minutes=15.0, vaccine_type="B"),
            ThermalRecord(device_id="DEV2", timestamp=datetime(2025, 1, 1, 12, 15, 0), temperature=4.5, duration_minutes=15.0, vaccine_type="B"),
        ]

        result = ColdChainContinuityValidator.validate(records, device_id="DEV2")

        assert result.valid is False
        assert len(result.gaps) == 1
        assert result.gaps[0].duration_hours == 3.25
        assert "توجد فجوات زمنية حرجة" in result.warning

    def test_validate_with_insufficient_records_returns_valid(self):
        records = [
            ThermalRecord(device_id="DEV3", timestamp=datetime(2025, 1, 1, 9, 0, 0), temperature=3.0, duration_minutes=15.0, vaccine_type="C"),
        ]

        result = ColdChainContinuityValidator.validate(records, device_id="DEV3")

        assert result.valid is True
        assert result.gaps == []
        assert result.warning == "بيانات قليلة"
