# tests/reporting/test_centers_report_snapshot.py
import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.reporting.csv_reporter import generate_centers_report

@dataclass
class MockCenterDTO:
    id: str
    name: str
    device_ids: List[str]
    decision: str
    vvm_stage: str
    decision_reasons: List[str]
    stats: Dict[str, Any] = field(default_factory=dict)
    ft2_entries_count: int = 0
    ft2_entries: List = field(default_factory=list)
    alert_level: Optional[str] = None
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    category_display: Optional[str] = None
    has_warning: bool = False

@pytest.fixture
def sample_centers():
    return [
        MockCenterDTO(
            id="C1",
            name="Center 1",
            device_ids=["D1"],
            decision="ACCEPTED",
            vvm_stage="STAGE_1",
            decision_reasons=["All entries within custom range"],
            stats={"min_temp": 2.0, "max_temp": 8.0, "avg_temp": 5.0, "heat_duration": 0},
            ft2_entries_count=1
        ),
        MockCenterDTO(
            id="C2",
            name="Center 2",
            device_ids=["D2"],
            decision="REJECTED",
            vvm_stage="STAGE_2",
            decision_reasons=["Temp 12.0 > max 8.0"],
            stats={"min_temp": 4.0, "max_temp": 12.0, "avg_temp": 10.0, "heat_duration": 60},
            ft2_entries_count=1
        ),
    ]

def test_centers_report_snapshot(tmp_path, sample_centers, snapshot):
    """
    Snapshot Test لتقرير المراكز.
    """
    output_file = tmp_path / "centers_report.tsv"
    generate_centers_report(sample_centers, str(output_file))
    
    content = output_file.read_text(encoding="utf-8")
    
    snapshot.assert_match(content, "centers_report_snapshot.tsv")
