# src/presentation/reporting/unified_pdf_generator.py
"""
DEPRECATED: UnifiedPDFGenerator moved to Clean Architecture.

This file is a compatibility shim. Use the new Clean Architecture approach:

    from src.application.app_composer import AppComposer
    pdf_uc = AppComposer.create_generate_pdf_report_uc()
    pdf_bytes = pdf_uc.execute_device_report(dto)

For legacy code, use:

    from src.infrastructure.pdf.arabic_font_manager import UnifiedPDFGeneratorWrapper
    wrapper = UnifiedPDFGeneratorWrapper()
    pdf_bytes = wrapper.render(dto)

This shim will be removed in Phase 7.
"""

import warnings
from typing import Any

warnings.warn(
    "UnifiedPDFGenerator is deprecated. Use Clean Architecture with GeneratePDFReportUseCase instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for compatibility
from src.infrastructure.pdf.arabic_font_manager import UnifiedPDFGeneratorWrapper as UnifiedPDFGenerator

__all__ = ["UnifiedPDFGenerator"]