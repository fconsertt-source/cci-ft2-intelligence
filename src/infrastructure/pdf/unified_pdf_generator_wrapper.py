# src/infrastructure/pdf/unified_pdf_generator_wrapper.py
"""
Re-export shim — Phase 5 Refactor (2026-03-10)

جميع الكلاسات والدوال تُستورد الآن من:
  src.infrastructure.pdf.arabic_font_manager

هذا الملف محفوظ للتوافق مع الاستيرادات الموجودة.
سيُحذف في Phase 6 بعد تحديث جميع المستوردين.

@DEPRECATED: استخدم src.infrastructure.pdf.arabic_font_manager مباشرة
@WILL_DELETE: Phase 6 — بعد 2026-03-17
"""

from src.infrastructure.pdf.arabic_font_manager import (  # noqa: F401
    ARABIC_FONT_NAME, FALLBACK_FONT_NAME, ArabicFontManager,
    ArabicPDFGenerator, LegacyPDFGenerator, UnifiedPDFGeneratorWrapper,
    _register_arabic_font, get_pdf_generator, register_arabic_font,
    shape_arabic_text)

__all__ = [
    "ARABIC_FONT_NAME",
    "FALLBACK_FONT_NAME",
    "ArabicFontManager",
    "ArabicPDFGenerator",
    "LegacyPDFGenerator",
    "UnifiedPDFGeneratorWrapper",
    "_register_arabic_font",
    "get_pdf_generator",
    "register_arabic_font",
    "shape_arabic_text",
]
