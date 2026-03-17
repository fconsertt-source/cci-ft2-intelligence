# src/domain/evidence/evidence_integrity_report.py
"""تقرير تكامل الأدلة الرقمية"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .evidence_grade import EvidenceGrade
from .verification_result import VerificationStatus


@dataclass(frozen=True)
class EvidenceIntegrityReport:
    """
    تقرير شامل عن سلامة الأدلة الرقمية

    يحتوي على:
    - حالة التوقيع
    - نتيجة المقارنة
    - الدرجة النهائية
    - تفاصيل للتدقيق
    """

    # 🏷️ الهوية
    device_id: str
    serial: str

    # 🔐 حالة التوقيع (البوابة الأمنية الأولى)
    signature_status: VerificationStatus

    # 📊 نتيجة المقارنة بين المصدرين
    cross_check_result: str  # "FULL_CONSISTENCY", "MINOR_INCONSISTENCY", etc.

    # 🎯 الدرجة النهائية
    overall_grade: EvidenceGrade

    # 📅 الطابع الزمني
    verification_timestamp: datetime

    # 🔒 الهاشات للتحقق من السلامة
    txt_hash: str
    pdf_hash: Optional[str]

    # 📝 تفاصيل إضافية
    details: Optional[str] = None

    # 📈 القيم الحرارية (من المقارنة)
    min_temperature: Optional[Decimal] = None
    max_temperature: Optional[Decimal] = None
    avg_temperature: Optional[Decimal] = None

    def is_trusted(self) -> bool:
        """هل الأدلة موثوقة؟ (درجة A+ أو A أو B)"""
        return self.overall_grade in [
            EvidenceGrade.A_PLUS,
            EvidenceGrade.A,
            EvidenceGrade.B,
        ]

    def requires_review(self) -> bool:
        """هل تحتاج مراجعة بشرية؟ (درجة C)"""
        return self.overall_grade == EvidenceGrade.C

    def is_rejected(self) -> bool:
        """هل تم رفض الأدلة؟ (درجة F)"""
        return self.overall_grade == EvidenceGrade.F

    def __str__(self) -> str:
        return (
            f"Evidence Report [{self.serial}] "
            f"Grade: {self.overall_grade.value} "
            f"Signature: {self.signature_status.value} "
            f"Cross-check: {self.cross_check_result}"
        )
