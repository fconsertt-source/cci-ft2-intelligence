# tests/reporting/test_centers_report_snapshot.py
import importlib.util
import sys
from pathlib import Path

import pytest

# skip if snapshot fixture (pytest-snapshot plugin) not available
if importlib.util.find_spec("pytest_snapshot") is None:
    pytest.skip("pytest-snapshot plugin not available", allow_module_level=True)

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.presentation.reporting.csv_reporter import generate_centers_report


class MockCenterDTO:
    """Mock لـ CenterDTO للاختبار"""

    def __init__(self, **kwargs):
        # تخزين القيم الداخلية
        self._id = kwargs.get("id", "")
        self._name = kwargs.get("name", "")
        self._device_ids = kwargs.get("device_ids", [])
        self._decision = kwargs.get("decision", "UNKNOWN")
        self._vvm_stage = kwargs.get("vvm_stage", "NONE")
        self._decision_reasons = kwargs.get("decision_reasons", [])
        self._alert_level = kwargs.get("alert_level", None)
        self._stability_budget_consumed_pct = kwargs.get(
            "stability_budget_consumed_pct", 0.0
        )
        self._thaw_remaining_hours = kwargs.get("thaw_remaining_hours", None)
        self._category_display = kwargs.get("category_display", None)
        self._has_warning_flag = kwargs.get("has_warning", False)
        self._ft2_entries_count = kwargs.get("ft2_entries_count", 0)
        self._ft2_entries = kwargs.get("ft2_entries", [])

        # إعداد stats
        self.stats = kwargs.get("stats", {})
        self.stats.setdefault("judgment_risk", "SAFE")
        self.stats.setdefault("judgment_icon", "🟢")
        self.stats.setdefault("confidence", 1.0)
        self.stats.setdefault("requires_review", False)
        self.stats.setdefault("her_percentage", 0.0)
        self.stats.setdefault("ccm_index", "0")
        self.stats.setdefault("judgment_narrative", "")
        self.stats.setdefault("avg_temp", None)
        self.stats.setdefault("min_temp", None)
        self.stats.setdefault("max_temp", None)
        self.stats.setdefault("has_freeze", False)
        self.stats.setdefault("has_ccm_violation", False)
        self.stats.setdefault("her_ratio", 0.0)

    # الخصائص الأساسية
    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def device_ids(self):
        return self._device_ids

    @property
    def decision(self):
        return self._decision

    @property
    def vvm_stage(self):
        return self._vvm_stage

    @property
    def decision_reasons(self):
        return self._decision_reasons

    @property
    def alert_level(self):
        return self._alert_level

    @property
    def stability_budget_consumed_pct(self):
        return self._stability_budget_consumed_pct

    @property
    def thaw_remaining_hours(self):
        return self._thaw_remaining_hours

    @property
    def category_display(self):
        return self._category_display

    @property
    def ft2_entries(self):
        return self._ft2_entries

    @property
    def ft2_entries_count(self) -> int:
        return self._ft2_entries_count

    @property
    def has_warning(self) -> bool:
        return self._has_warning_flag

    # خصائص من stats
    @property
    def avg_temperature(self) -> str:
        avg = self.stats.get("avg_temp")
        return f"{avg:.2f}" if avg is not None else "N/A"

    @property
    def min_temperature(self) -> str:
        min_t = self.stats.get("min_temp")
        return f"{min_t:.2f}" if min_t is not None else "N/A"

    @property
    def max_temperature(self) -> str:
        max_t = self.stats.get("max_temp")
        return f"{max_t:.2f}" if max_t is not None else "N/A"

    @property
    def has_freeze(self) -> bool:
        return self.stats.get("has_freeze", False)

    @property
    def has_ccm_violation(self) -> bool:
        return self.stats.get("has_ccm_violation", False)

    @property
    def her_ratio(self) -> float:
        return float(self.stats.get("her_ratio", 0.0))

    @property
    def ccm_index(self) -> str:
        return str(self.stats.get("ccm_index", "0"))

    @property
    def judgment_risk(self) -> str:
        return self.stats.get("judgment_risk", "SAFE")

    @property
    def judgment_icon(self) -> str:
        return self.stats.get("judgment_icon", "🟢")

    @property
    def confidence(self) -> float:
        return float(self.stats.get("confidence", 0.0))

    @property
    def requires_review(self) -> bool:
        return self.stats.get("requires_review", False)

    @property
    def her_percentage(self) -> float:
        return float(self.stats.get("her_percentage", 0.0))

    @property
    def judgment_narrative(self) -> str:
        return self.stats.get("judgment_narrative", "")

    @property
    def has_error(self) -> bool:
        return self.decision.upper() in ["CRITICAL", "UNSAFE", "REJECT"]


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
            stats={
                "min_temp": 2.0,
                "max_temp": 8.0,
                "avg_temp": 5.0,
                "heat_duration": 0,
                "judgment_risk": "SAFE",
                "judgment_icon": "🟢",
                "confidence": 0.95,
                "requires_review": False,
                "her_percentage": 0.0,
                "ccm_index": "0",
            },
            ft2_entries_count=1,
        ),
        MockCenterDTO(
            id="C2",
            name="Center 2",
            device_ids=["D2"],
            decision="REJECTED",
            vvm_stage="STAGE_2",
            decision_reasons=["Temp 12.0 > max 8.0"],
            stats={
                "min_temp": 4.0,
                "max_temp": 12.0,
                "avg_temp": 10.0,
                "heat_duration": 60,
                "judgment_risk": "HIGH",
                "judgment_icon": "🔴",
                "confidence": 0.98,
                "requires_review": True,
                "her_percentage": 50.0,
                "ccm_index": "A",
            },
            ft2_entries_count=1,
        ),
    ]


def test_centers_report_snapshot(tmp_path, sample_centers, snapshot):
    """
    Snapshot Test لتقرير المراكز.
    """
    output_file = tmp_path / "centers_report.tsv"
    generate_centers_report(sample_centers, str(output_file))

    content = output_file.read_text(encoding="utf-8")

    snapshot.assert_match(content, "centers_report.tsv")
