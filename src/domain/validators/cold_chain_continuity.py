from __future__ import annotations

from datetime import timedelta
from typing import Iterable, List, Optional

from src.domain.entities.thermal_record import ThermalRecord
from src.domain.value_objects.cold_chain_analysis_result import (
    ColdChainAnalysisResult,
    ColdChainGap,
)


class ColdChainContinuityValidator:
    """يكشف الفجوات الزمنية الحرجة التي قد تؤثر على دقة HER/VVM/CCM"""
    MAX_GAP = timedelta(hours=2)

    @classmethod
    def validate(
        cls,
        records: Iterable[ThermalRecord],
        device_id: str,
    ) -> ColdChainAnalysisResult:
        records_list: List[ThermalRecord] = list(records)

        if len(records_list) < 2:
            return ColdChainAnalysisResult(valid=True, gaps=[], warning="بيانات قليلة")

        sorted_records = sorted(records_list, key=lambda record: record.timestamp)
        gaps = []

        for previous, current in zip(sorted_records, sorted_records[1:]):
            delta = current.timestamp - previous.timestamp
            if delta > cls.MAX_GAP:
                gaps.append(
                    ColdChainGap(start=current.timestamp, duration_hours=delta.total_seconds() / 3600.0)
                )

        if not gaps:
            return ColdChainAnalysisResult(valid=True, gaps=[], warning=None)

        return ColdChainAnalysisResult(
            valid=False,
            gaps=gaps,
            warning=f"توجد فجوات زمنية حرجة في جهاز {device_id} قد تؤثر على دقة الحسابات",
        )
