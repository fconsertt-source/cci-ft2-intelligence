"""Lightweight PDF generator shim used when no concrete PDF generator
implementation is available. Tests will typically patch `PDFReportGenerator`.
"""

from __future__ import annotations

class PDFReportGenerator:
    """Shim class for tests and lightweight execution.

    Production deployments can provide a richer implementation in
    `src.reporting.pdf_generator` that implements the same `generate_report`
    method signature.
    """

    def __init__(self, *args, **kwargs) -> None:
        pass

    def generate_report(self, tsv_path: str) -> str:
        """Generate a PDF from the TSV at `tsv_path`.

        This shim raises NotImplementedError to indicate that a real
        implementation should be provided by the deployment or patched in
        tests.
        """
        raise NotImplementedError("PDFReportGenerator.generate_report is not implemented in this environment")
