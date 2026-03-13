"""Compatibility module for legacy visual report tests.
This module exposes a simple ``UnifiedPDFGenerator`` class so that
patching in older tests continues to work even though the real implementation
has moved to the adapters layer.
"""

# reuse existing ReportType enum from domain; this keeps the compatibility
# layer thin and ensures scripts/tests that expect ``ReportType`` continue to
# work.
from src.domain.enums.report_scope import ReportType
from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
    UnifiedPDFGeneratorWrapper,
)


class UnifiedPDFGenerator(UnifiedPDFGeneratorWrapper):
    """Legacy name for the unified wrapper (kept for compatibility)."""

    pass


# expose ReportType for importers of this module
__all__ = ["UnifiedPDFGenerator", "ReportType"]
