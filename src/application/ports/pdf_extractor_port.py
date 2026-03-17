#!/usr/bin/env python3
"""
واجهة مجردة لمستخرج بيانات PDF (PdfExtractorPort)

هذا Port يسمح بعزل البنية التحتية لاستخراج PDF
عن منطق الأعمال في Use Cases و Validators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Protocol


class PdfExtractorPort(Protocol):
    """
    واجهة مستخرج بيانات PDF.

    يتبع مبدأ Dependency Inversion:
    - High-level modules (Validators, UseCases) لا تعتمد على low-level details
    - كلاهما يعتمد على هذه الواجهة المجردة
    """

    def extract(self, pdf_path: Path) -> Dict[str, Any]:
        """
        استخراج البيانات من ملف PDF.

        Args:
            pdf_path: مسار ملف PDF

        Returns:
            dict: بيانات مستخرجة تحتوي على:
                - serial (str): الرقم التسلسلي للجهاز
                - min_temp (float): أقل درجة حرارة مسجلة
                - max_temp (float): أعلى درجة حرارة مسجلة
                - avg_temp (float): متوسط درجة الحرارة
                - readings_count (int): عدد القراءات
                - alarm_detected (bool): هل تم رصد إنذار حراري
        """
        ...
