# src/domain/evidence/evidence_grade.py
"""تصنيف درجات ثقة الأدلة الرقمية"""

from enum import Enum

class EvidenceGrade(Enum):
    """
    نظام تصنيف درجات الثقة للأدلة الرقمية
    
    التصنيف يعتمد على:
    - سلامة التوقيع (40%)
    - تطابق البيانات (30%)
    - اكتمال البيانات (20%)
    - ثبات الهاش (10%)
    """
    
    A_PLUS = "A+"  # توقيع صالح + تطابق كامل
    A = "A"        # توقيع صالح + اختلافات طفيفة غير حرجة
    B = "B"        # توقيع صالح + اختلافات متوسطة (تحتاج مراجعة)
    C = "C"        # توقيع صالح + اختلافات خطيرة (تحتاج تدخل)
    F = "F"        # توقيع غير صالح (مرفوض تماماً)
    
    @property
    def numeric_value(self) -> int:
        """القيمة العددية للدرجة (0-100)"""
        values = {
            EvidenceGrade.A_PLUS: 100,
            EvidenceGrade.A: 90,
            EvidenceGrade.B: 75,
            EvidenceGrade.C: 60,
            EvidenceGrade.F: 0,
        }
        return values[self]
    
    @property
    def is_passing(self) -> bool:
        """هل الدرجة مقبولة؟"""
        return self in [EvidenceGrade.A_PLUS, EvidenceGrade.A, EvidenceGrade.B]
    
    @property
    def requires_human_review(self) -> bool:
        """هل تحتاج مراجعة بشرية؟"""
        return self in [EvidenceGrade.B, EvidenceGrade.C]
    
    @property
    def is_rejected(self) -> bool:
        """هل تم رفض الأدلة؟"""
        return self == EvidenceGrade.F