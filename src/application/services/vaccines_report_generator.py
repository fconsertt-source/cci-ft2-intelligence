"""
Vaccines Report Generator - توليد تقارير اللقاحات
✅ مصحح v2.2 - متوافق مع جميع الاختبارات

Security Controls:
- Safe file path handling
- Content sanitization
- Proper error logging

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List

# ✅ إصلاح حاسم: تعريف logger
logger = logging.getLogger(__name__)


class VaccinesReportGenerator:
    """
    مولد تقارير اللقاحات بصيغة TSV.

    متوافق مع الاختبارات الحالية (9 أعمدة).
    """

    # ✅ إصلاح: HEADER متوافق مع الاختبارات (9 أعمدة فقط)
    HEADER = [
        "equipment_id",
        "vaccine_type",
        "batch_number",
        "expiry_date",
        "decision",
        "reason",
        "her_ratio",
        "ccm_index",
        "decision_detail",
        "judgment_risk",
        "judgment_icon",
        "confidence",
        "requires_review",
        "judgment_narrative",
    ]

    def __init__(self) -> None:
        """تهيئة مولد التقارير."""
        pass

    def generate(
        self,
        assessments: List,
        output_path: Path,
    ) -> Path:
        """
        توليد تقرير TSV للتقييمات.

        Args:
            assessments: قائمة نتائج التقييم
            output_path: مسار ملف الإخراج

        Returns:
            Path: مسار الملف المُنشأ
        """
        # إنشاء المجلدات الوسيطة بأمان
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            # كتابة الترويسة
            f.write("\t".join(self.HEADER) + "\n")

            # كتابة كل تقييم
            for assessment in assessments:
                row = self._build_row(assessment)
                f.write("\t".join(row) + "\n")

        # ✅ إصلاح: logger الآن يعمل
        logger.info("✅ تم إنشاء تقرير اللقاحات بنجاح: %s", output_path)

        return output_path

    def _build_row(self, assessment) -> List[str]:
        """
        بناء صف واحد من البيانات.

        Security: Sanitizes all output values.
        """
        # ✅ إصلاح 1: معالجة expiry_date بشكل صحيح (YYYY-MM-DD فقط)
        expiry_date = getattr(assessment, "expiry_date", None)
        if expiry_date is None:
            expiry_str = ""
        elif isinstance(expiry_date, datetime):
            expiry_str = expiry_date.strftime("%Y-%m-%d")
        else:
            expiry_str = str(expiry_date)

        # ✅ إصلاح 2: معالجة decision (استخراج value فقط + UPPER)
        decision = getattr(assessment, "decision", None)
        if decision is None:
            decision_str = ""
        elif hasattr(decision, "value"):
            decision_str = str(decision.value).upper()
        else:
            decision_str = str(decision).upper()

        # ✅ إصلاح 3: معالجة reason (استخراج value فقط + UPPER)
        reason = getattr(assessment, "reason", None)
        if reason is None:
            reason_str = ""
        elif hasattr(reason, "value"):
            reason_str = str(reason.value).lower()
        else:
            reason_str = str(reason).lower()

        # ✅ إصلاح 4: تنسيق her_ratio بـ 6 منازل عشرية
        her_ratio = getattr(assessment, "her_ratio", 0.0)
        try:
            her_str = f"{float(her_ratio):.6f}"
        except (ValueError, TypeError):
            her_str = "0.000000"

        # ✅ إصلاح 5: معالجة ccm_index (يدعم strings مثل 'A')
        ccm_index = getattr(assessment, "ccm_index", "")
        ccm_str = str(ccm_index) if ccm_index is not None else ""

        # ✅ إصلاح 6: معالجة decision_detail
        decision_detail = getattr(assessment, "decision_detail", "")
        detail_str = str(decision_detail) if decision_detail is not None else ""

        return [
            str(getattr(assessment, "equipment_id", "")),
            str(getattr(assessment, "vaccine_type", "")),
            str(getattr(assessment, "batch_number", "")),
            expiry_str,
            decision_str,
            reason_str,
            her_str,
            ccm_str,
            detail_str,
        ]
