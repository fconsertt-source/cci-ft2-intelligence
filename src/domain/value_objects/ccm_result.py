# src/domain/value_objects/ccm_result.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CCMResult:
    """
    نتيجة حساب Cold Chain Monitor (CCM).

    يقيس التراكم الحراري بطريقتين مستقلتين:
    - Delta: مجموع الفروقات المطلقة في درجة الحرارة
    - AUC:   المساحة تحت المنحنى فوق درجة الحرارة الأساسية (degree-minutes)

    القيمة النقية — لا قرار، لا حكم.
    التفسير مسؤولية الطبقة العليا فقط.
    """

    # مجموع الفروقات المطلقة في درجة الحرارة (طريقة CCM الكلاسيكية)
    ccm_delta: float

    # المساحة تحت المنحنى فوق درجة الأساس (degree-minutes)
    ccm_auc: float

    # درجة الحرارة الأساسية المستخدمة في AUC (عادةً 8.0°C)
    base_temp_used: float

    # عدد القراءات
    readings_count: int

    # المدة الكلية بالدقائق المغطاة بالقراءات
    total_duration_minutes: float

    @property
    def auc_per_hour(self) -> float:
        """متوسط degree-minutes في الساعة (لتسهيل المقارنة)"""
        hours = self.total_duration_minutes / 60.0
        if hours <= 0:
            return 0.0
        return self.ccm_auc / hours

    @property
    def has_heat_exposure(self) -> bool:
        """هل كان هناك تعرض حراري فوق درجة الأساس؟"""
        return self.ccm_auc > 0.0

    def __repr__(self) -> str:
        return (
            f"CCMResult("
            f"ccm_delta={self.ccm_delta:.2f}, "
            f"ccm_auc={self.ccm_auc:.2f} deg-min, "
            f"base_temp={self.base_temp_used}°C, "
            f"duration={self.total_duration_minutes:.1f}min)"
        )
