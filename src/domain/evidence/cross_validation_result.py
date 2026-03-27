# src/domain/evidence/cross_validation_result.py
"""نتيجة المقارنة بين مصدري البيانات"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .evidence_grade import EvidenceGrade


@dataclass(frozen=True)
class CrossValidationResult:
    """نتيجة مقارنة البيانات بين ملفات TXT و PDF"""

    # 🎯 الدرجة النهائية للمقارنة
    grade: EvidenceGrade

    # 📊 نتيجة المقارنة
    result: str  # "FULL_CONSISTENCY", "SERIAL_MISMATCH", etc.

    # 📝 تفاصيل
    details: Optional[str] = None

    # 📈 القيم المستخلصة (للمقارنة)
    txt_serial: Optional[str] = None
    pdf_serial: Optional[str] = None
    txt_min_temp: Optional[Decimal] = None
    pdf_min_temp: Optional[Decimal] = None
    txt_max_temp: Optional[Decimal] = None
    pdf_max_temp: Optional[Decimal] = None

    def __str__(self) -> str:
        return f"CrossValidation: {self.result} (Grade: {self.grade.value})"
