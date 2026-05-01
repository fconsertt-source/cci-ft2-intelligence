from datetime import datetime, timedelta

from src.domain.services.scientific_reference_service import ScientificReferenceService
from src.domain.value_objects.temperature_entry import TemperatureEntry


class TestScientificReferenceService:

    def test_analyze_returns_reference_her_and_mkt(self):
        service = ScientificReferenceService()
        base_time = datetime(2026, 1, 1, 0, 0, 0)

        entries = [
            TemperatureEntry(temperature=5.0, timestamp=base_time, duration_minutes=60.0),
            TemperatureEntry(temperature=10.0, timestamp=base_time + timedelta(hours=1), duration_minutes=60.0),
            TemperatureEntry(temperature=8.0, timestamp=base_time + timedelta(hours=2), duration_minutes=60.0),
        ]

        result = service.analyze(entries=entries, vaccine_type="OPV")

        assert result["reference_audit_enabled"] is True
        assert result["reference_her_ratio"] >= 0.0
        assert result["reference_mkt_c"] >= 0.0
        assert result["reference_source"] == "WHO/IVB/06.10 Table 1"
        assert result["reference_traceability"]["engine"] == "ArrheniusReferenceExposureEngine"
