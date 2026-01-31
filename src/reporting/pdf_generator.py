"""Lightweight PDF generator shim used when no concrete PDF generator
implementation is available. Tests will typically patch `PDFReportGenerator`.
"""

from __future__ import annotations

import os
from typing import Optional


class PDFReportGenerator:
    """Shim class for tests and lightweight execution.

    Production deployments can provide a richer implementation that
    implements the same `generate_report(tsv_path) -> str` API.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        self.output_dir = output_dir or "data/output/reports"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, tsv_path: str) -> str:
        """Generate a PDF path for the given TSV. Shim raises
        NotImplementedError by default to signal tests or deployments should
        provide an implementation (tests patch `PDFReportGenerator`).
        """
        raise NotImplementedError("PDFReportGenerator.generate_report is not implemented in this environment")


def generate_pdf_report() -> Optional[str]:
    """Helper used by scripts: if a PDF generator implementation is present,
    it should be patched in tests; otherwise the shim raises.
    """
    tsv_path = "data/output/centers_report.tsv"
    if not os.path.exists(tsv_path):
        return None
    gen = PDFReportGenerator()
    return gen.generate_report(tsv_path)

