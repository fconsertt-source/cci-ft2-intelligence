import pytest
from domain.services.device_id_extractor import DeviceIDExtractor

class TestDeviceIDExtractor:
    def test_extracts_from_standard_ft2_filename(self):
        result = DeviceIDExtractor.extract(
            "130600112663_202603251042.txt"
        )
        assert result == "130600112663"

    def test_extracts_from_prefixed_filename(self):
        result = DeviceIDExtractor.extract(
            "safe_hospital_130600112764.csv"
        )
        assert result == "130600112764"

    def test_raises_for_unknown_format(self):
        with pytest.raises(ValueError, match="لا يمكن استخراج"):
            DeviceIDExtractor.extract("unknown_file.csv")

    def test_is_valid_device_id_correct(self):
        assert DeviceIDExtractor.is_valid_device_id("130600112663") is True

    def test_is_valid_device_id_too_short(self):
        assert DeviceIDExtractor.is_valid_device_id("13060") is False