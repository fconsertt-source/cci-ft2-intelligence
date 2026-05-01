from __future__ import annotations

import pandas as pd
from datetime import timedelta
from typing import Iterable, List

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.ports.cold_chain_analyzer_port import ColdChainAnalyzerPort
from src.domain.value_objects.cold_chain_analysis_result import (
    ColdChainAnalysisResult,
    ColdChainGap,
)


class PandasColdChainAnalyzer(ColdChainAnalyzerPort):
    """Infrastructure adapter that confines Pandas usage outside the Domain."""

    MAX_GAP = timedelta(hours=2)

    def analyze(self, records: List[ThermalRecord]) -> ColdChainAnalysisResult:
        if not records:
            return ColdChainAnalysisResult(valid=True, gaps=[], warning="بيانات قليلة")

        rows = [
            {
                "timestamp": record.timestamp,
                "device_id": record.device_id,
            }
            for record in records
        ]
        df = pd.DataFrame(rows)
        if df.empty or len(df) < 2:
            return ColdChainAnalysisResult(valid=True, gaps=[], warning="بيانات قليلة")

        df = df.sort_values("timestamp")
        gaps = df["timestamp"].diff().dropna()
        critical_gaps = gaps[gaps > self.MAX_GAP]

        if critical_gaps.empty:
            return ColdChainAnalysisResult(valid=True, gaps=[], warning=None)

        return ColdChainAnalysisResult(
            valid=False,
            gaps=[
                ColdChainGap(start=idx, duration_hours=gap.total_seconds() / 3600.0)
                for idx, gap in critical_gaps.items()
            ],
            warning=f"توجد فجوات زمنية حرجة في جهاز {records[0].device_id} قد تؤثر على دقة الحسابات",
        )
