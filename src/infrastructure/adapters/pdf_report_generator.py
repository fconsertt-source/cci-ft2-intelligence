from __future__ import annotations
from pathlib import Path
from src.application.ports.i_reporter import IReporter
from src.application.dtos.analysis_result_dto import AnalysisResultDTO


class PdfReportGenerator(IReporter):
    """Minimal PDF generator for Phase 5 architectural proof.
    
    Responsibilities:
      - Implements IReporter Port explicitly
      - Lives ONLY in infrastructure/adapters/
      - Contains ZERO business logic (placeholder only)
      - Proves the evolution pattern is safe
    
    Boundaries:
      ✅ Depends ONLY on IReporter Port (abstraction)
      ❌ NO dependency on domain/entities
      ❌ NO business logic (decision rules belong in Use Cases)
    """
    
    def __init__(self, output_dir: str = "reports") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, result: AnalysisResultDTO) -> None:
        """
        Generates a PDF report placeholder.
        ⚠️ Minimal implementation: only creates a placeholder file.
        No domain logic or formatting complexity.
        """
        output_path = self.output_dir / f"{result.vaccine_id}.pdf"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"PDF Report for Vaccine: {result.vaccine_id}\n")
            f.write(f"Status: {result.status.value}\n")
            f.write(f"Decision reasons: {', '.join(result.decision_reasons)}\n")
            f.write(f"Recommendations: {', '.join(result.recommendations)}\n")
        print(f"✅ PdfReportGenerator: placeholder report created at {output_path}")