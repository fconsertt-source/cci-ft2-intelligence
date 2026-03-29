import tempfile
from pathlib import Path
from typing import List, Optional
import pandas as pd

from src.application.dtos.center_dto import CenterDTO
from src.infrastructure.pdf.unified_pdf_generator import UnifiedPDFGenerator, ReportType


class UnifiedPDFGeneratorDTOAdapter:
    """
    Adapter to generate PDF reports from CenterDTO objects.
    Converts DTOs to a DataFrame, writes temporary TSV, and delegates to UnifiedPDFGenerator.
    """

    def __init__(self, output_dir: str = "data/output/reports", language: str = "ar"):
        self.generator = UnifiedPDFGenerator(language=language, output_dir=output_dir)

    def _center_to_record(self, center: CenterDTO) -> dict:
        """Convert a CenterDTO to a dictionary with fields expected by the report generator."""
        return {
            "center_id": center.id,
            "center_name": center.name,
            "category_display": center.category_display or "General",
            "alert_level": center.alert_level or "GREEN",
            "stability_budget_consumed_pct": getattr(center, "stability_budget_consumed_pct", 0.0),
            "thaw_remaining_hours": getattr(center, "thaw_remaining_hours", None),
            "avg_temperature": getattr(center, "avg_temperature", None),
            "has_freeze": getattr(center, "has_freeze", False),
            "has_ccm_violation": getattr(center, "has_ccm_violation", False),
            "decision_reasons": "; ".join(getattr(center, "decision_reasons", [])) if getattr(center, "decision_reasons", None) else "",
        }

    def generate_from_centers(
        self,
        centers: List[CenterDTO],
        report_type: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Generate PDF report from a list of CenterDTOs.
        report_type: 'official', 'technical', or 'arabic'
        """
        # Convert to records
        records = [self._center_to_record(c) for c in centers]
        df = pd.DataFrame(records)

        # Write temporary TSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False, encoding="utf-8") as tmp:
            df.to_csv(tmp.name, sep="\t", index=False)
            tmp_path = tmp.name

        # Delegate to the core generator
        try:
            result_path = self.generator.generate(report_type, tmp_path, filename=filename)
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)

        return result_path