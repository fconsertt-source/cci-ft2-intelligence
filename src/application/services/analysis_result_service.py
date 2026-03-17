# src/application/services/analysis_result_service.py
from __future__ import annotations

from typing import Tuple

from src.domain.dtos.analysis_result_dto import (AnalysisResultDTO,
                                                 VaccineStatus)


class AnalysisResultService:
    """Service that enriches AnalysisResultDTO with business logic.

    Extracted from evolutionary artifact: run_windows_friendly.ps1
    Preserved value: battle-tested decision logic for vaccine recommendations.
    """

    @staticmethod
    def get_recommended_action(dto: AnalysisResultDTO) -> Tuple[str, ...]:
        """Extracted from run_windows_friendly.ps1 — battle-tested logic."""
        recommendations = []

        # 1. Base on Status (preserved from original artifact)
        if dto.status == VaccineStatus.DISCARD:
            recommendations.extend(
                [
                    "❌ يتم استبعاد هذا اللقاح فوراً من الاستخدام.",
                    "🚩 يجب التحقق من وحدة التبريد وإصلاح الخلل الفني.",
                ]
            )
        elif dto.status == VaccineStatus.PARTIAL:
            recommendations.append("⚠️ يستخدم هذا اللقاح مع الأولوية (استخدام أولاً).")

        # 2. Base on Alert Level (preserved from original artifact)
        if dto.alert_level == "YELLOW":
            recommendations.append("🟡 تنبيه: استهلاك مرتفع للميزانية الحرارية.")

        # ... باقي المنطق المُستخرج من السكربت الأصلي ...

        return tuple(recommendations)
