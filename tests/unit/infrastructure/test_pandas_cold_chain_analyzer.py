import pytest
from datetime import datetime

from src.domain.entities.thermal_record import ThermalRecord
from src.infrastructure.adapters.pandas_cold_chain_analyzer import PandasColdChainAnalyzer


def test_pandas_cold_chain_analyzer_detects_gap():
    pytest.importorskip("pandas")
    analyzer = PandasColdChainAnalyzer()
    records = [
        ThermalRecord(device_id="DEV4", timestamp=datetime(2025, 1, 1, 9, 0, 0), temperature=3.0, duration_minutes=15.0, vaccine_type="D"),
        ThermalRecord(device_id="DEV4", timestamp=datetime(2025, 1, 1, 12, 30, 0), temperature=3.0, duration_minutes=15.0, vaccine_type="D"),
    ]

    result = analyzer.analyze(records)

    assert result.valid is False
    assert len(result.gaps) == 1
    assert result.gaps[0].duration_hours == 3.5
    assert result.warning is not None
