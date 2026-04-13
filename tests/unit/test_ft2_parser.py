import csv
from datetime import datetime

import pytest

from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
# استخدم النوع الفعلي الذي يرجعه الـ parser
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2EntryDTO as FT2Entry


class TestFT2Parser:

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """إنشاء ملف CSV مؤقت للاختبار"""
        d = tmp_path / "data"
        d.mkdir()
        p = d / "test_readings.csv"

        headers = ["device_id", "timestamp", "temperature", "vaccine_type", "batch"]
        rows = [
            ["FT2-001", "2023-10-01T10:00:00", "5.5", "Pfizer", "B123"],
            ["FT2-001", "2023-10-01T10:15:00", "6.0", "Pfizer", "B123"],
        ]

        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return str(p)

    def test_parse_valid_csv(self, sample_csv):
        """اختبار تحليل ملف FT2 CSV صالح"""
        entries = FT2Parser.parse_file(sample_csv)

        assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"
        assert isinstance(entries[0], FT2Entry), f"Expected FT2Entry type, got {type(entries[0])}"

        assert entries[0].device_id == "FT2-001"
        assert entries[0].temperature == 5.5
        assert isinstance(entries[0].timestamp, datetime)
        assert entries[0].timestamp.hour == 10

    def test_parse_invalid_file(self, tmp_path):
        """اختبار ملف فارغ"""
        p = tmp_path / "empty.csv"
        p.touch()
        entries = FT2Parser.parse_file(str(p))
        assert len(entries) == 0

    def test_parse_malformed_rows(self, tmp_path):
        """اختبار صفوف تالفة (يجب تخطي الصف السيء)"""
        d = tmp_path / "data_malformed"
        d.mkdir()
        p = d / "bad_readings.csv"

        with open(p, "w", newline="", encoding="utf-8") as f:
            f.write("device_id,temperature\n")
            f.write("FT2-001,invalid_temp\n")   # يجب تخطيه
            f.write("FT2-002,5.0\n")            # يجب قبوله

        entries = FT2Parser.parse_file(str(p))
        assert len(entries) == 1
        assert entries[0].device_id == "FT2-002"