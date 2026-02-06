import pytest
from datetime import datetime, timedelta
from src.infrastructure.adapters.ft2_reader.validator.ft2_validator import FT2Validator
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Entry

class TestFT2Validator:
    
    def test_validate_consistency_good(self):
        t0 = datetime.now()
        entries = [
            FT2Entry("d1", t0, 5.0, "v1", "b1"),
            FT2Entry("d1", t0 + timedelta(minutes=15), 5.0, "v1", "b1"),
            FT2Entry("d1", t0 + timedelta(minutes=30), 5.0, "v1", "b1"),
        ]
        
        result = FT2Validator.validate_temporal_consistency(entries)
        assert result["status"] == "GOOD"
        assert len(result["gaps"]) == 0
        assert result["total_entries"] == 3

    def test_validate_consistency_with_gaps(self):
        t0 = datetime.now()
        entries = [
            FT2Entry("d1", t0, 5.0, "v1", "b1"),
            # Gap of 3 hours (180 mins) -> Should trigger > 120 min gap detection
            FT2Entry("d1", t0 + timedelta(hours=3), 5.0, "v1", "b1"),
        ]
        
        result = FT2Validator.validate_temporal_consistency(entries)
        assert result["status"] == "WITH_GAPS"
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["minutes"] == 180.0

    def test_validate_insufficient_data(self):
        entries = [
            FT2Entry("d1", datetime.now(), 5.0, "v1", "b1")
        ]
        result = FT2Validator.validate_temporal_consistency(entries)
        assert result["status"] == "INSUFFICIENT_DATA"
