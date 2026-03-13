# src/domain/value_objects/her_result.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class HERResult:
    """
    نتيجة حساب Heat Exposure Ratio (HER).

    HER ratio = مجموع ساعات الانحلال المتراكمة / shelf_life_hours
    القيمة النقية — لا قرار، لا حكم. التفسير في RulesEngine.
    """

    # مجموع ساعات الانحلال الحراري المكافئ
    cumulative_degradation_hours: float

    # النسبة المستهلكة من الميزانية الحرارية (0.0–1.0+)
    her_ratio: float

    # عدد القراءات
    readings_count: int

    # معامل Q10 المستخدم
    q10_value_used: float

    # درجة الحرارة المرجعية المستخدمة
    reference_temp_used: float

    # علامات جودة البيانات — قابلة للتوسع في Phase لاحق
    # sampling_gap: True إذا اكتُشفت فجوة > max_gap_hours
    data_quality_flags: Dict[str, bool] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        """her_ratio ≥ 1.0 = تجاوز الميزانية الحرارية الكاملة"""
        return self.her_ratio >= 1.0

    @property
    def percentage_consumed(self) -> float:
        """النسبة المئوية المستهلكة"""
        return self.her_ratio * 100.0

    @property
    def has_sampling_gap(self) -> bool:
        """هل اكتُشفت فجوة في القياس؟"""
        return self.data_quality_flags.get("sampling_gap", False)