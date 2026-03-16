# src/application/services/vaccines_report_generator.py
"""مولد تقرير اللقاحات — B3 Pipeline Integration."""
from pathlib import Path
from typing import List

from src.domain.value_objects.vaccine_assessment_result import VaccineAssessmentResult


class VaccinesReportGenerator:
    """مولد تقرير اللقاحات للتصدير إلى TSV."""

    HEADER = [
        "equipment_id", "vaccine_type", "batch_number", "expiry_date",
        "decision", "reason", "her_ratio", "ccm_index", "decision_detail"
    ]

    def generate(
        self,
        assessments: List[VaccineAssessmentResult],
        output_path: Path,
    ) -> Path:
        """
        توليد ملف TSV من قائمة نتائج التقييم.
        
        Args:
            assessments: قائمة نتائج تقييم اللقاحات
            output_path: مسار ملف الإخراج (.tsv)
            
        Returns:
            Path: مسار الملف الذي تم إنشاؤه
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            # كتابة الرأس
            f.write("\t".join(self.HEADER) + "\n")
            
            # كتابة كل نتيجة باستخدام to_tsv_row() الموجودة
            for assessment in assessments:
                f.write(assessment.to_tsv_row() + "\n")

        return output_path