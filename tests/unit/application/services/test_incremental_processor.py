from datetime import datetime

from src.application.services.incremental_processor import IncrementalPipelineProcessor


class FakeRegistry:
    def __init__(self):
        self.marked = None

    def is_new_data(self, device_id, file_timestamp):
        return True

    def mark_processed(self, device_id, last_timestamp, filename, readings_count):
        self.marked = (device_id, last_timestamp, filename, readings_count)


class FakeStorage:
    def __init__(self):
        self.rows = {}

    def get_session_metadata(self, session_id):
        return {"rows": len(self.rows[session_id])} if session_id in self.rows else {}

    def read_session(self, session_id, columns=None, batch_size=5_000):
        return iter(self.rows[session_id])

    def write_session(self, session_id, readings, metadata=None):
        self.rows[session_id] = list(readings)
        return f"{session_id}.parquet"


class FakeReader:
    def __init__(self, rows):
        self.rows = rows

    def read_rows(self, csv_path):
        return iter(self.rows)


def test_process_file_merges_and_deduplicates_by_timestamp(tmp_path):
    registry = FakeRegistry()
    storage = FakeStorage()
    storage.rows["123"] = [
        {"timestamp": "2024-01-01T00:00:00", "temperature": "5.0"},
        {"timestamp": "2024-01-01T00:15:00", "temperature": "6.0"},
    ]
    reader = FakeReader([
        {"timestamp": "2024-01-01T00:15:00", "temperature": "7.0"},
        {"timestamp": "2024-01-01T00:30:00", "temperature": "4.5"},
    ])
    processor = IncrementalPipelineProcessor(registry, storage, reader)
    csv_path = tmp_path / "123_202401010030.csv"
    csv_path.write_text("timestamp,temperature\n", encoding="utf-8")

    result = processor.process_file(csv_path)

    assert result["status"] == "processed"
    assert result["new_readings"] == 2
    assert result["total_readings"] == 3
    assert storage.rows["123"][1]["temperature"] == "7.0"
    assert registry.marked == (
        "123",
        datetime(2024, 1, 1, 0, 30),
        "123_202401010030.csv",
        2,
    )
