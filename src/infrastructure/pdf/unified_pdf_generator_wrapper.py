#!/usr/bin/env python3
"""
🏆 ARABIC PDF RESCUE - INDESTRUCTIBLE EDITION (FIXED)
=======================================================
"""
import logging
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ARABIC_RESCUE] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# -----------------------------
# Arabic shaping (optional)
# -----------------------------
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    ARABIC_SHAPING_AVAILABLE = True
except ImportError:
    ARABIC_SHAPING_AVAILABLE = False
    logger.warning(
        "Arabic shaping libraries not installed. Visual display may be imperfect."
    )


def _shape_arabic_visual(text: str) -> str:
    if ARABIC_SHAPING_AVAILABLE and text:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            pass
    return text


# -----------------------------
# Font manager (simplified for reliability)
# -----------------------------
class ArabicFontManager:
    def __init__(self):
        self.font_name = "Helvetica"  # fallback, but we'll try to register a better one

    def register_font(self) -> str:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            logger.warning("ReportLab not available – using Helvetica")
            return "Helvetica"

        # Try embedded fonts first
        embedded_fonts = [
            ("Amiri", "assets/fonts/Amiri-Regular.ttf"),
            ("DejaVu", "assets/fonts/DejaVuSans.ttf"),
        ]
        for name, path in embedded_fonts:
            if Path(path).exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    logger.info(f"✅ Registered embedded font: {name}")
                    return name
                except Exception:
                    continue

        # Try system fonts
        system_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        for path in system_fonts:
            if Path(path).exists():
                try:
                    pdfmetrics.registerFont(TTFont("SystemFont", path))
                    logger.info(f"✅ Registered system font: {path}")
                    return "SystemFont"
                except Exception:
                    continue

        logger.warning(
            "No Arabic font found – using Helvetica (text extraction works, visual may be imperfect)"
        )
        return "Helvetica"


# -----------------------------
# DTO (assumed to exist in the project; we'll just use it)
# -----------------------------
# We won't redefine DeviceReportDTO here; it will be imported from application layer.


# -----------------------------
# Legacy generator (unchanged)
# -----------------------------
class LegacyPDFGenerator:
    def generate(self, report_type: str, data_path: Optional[str] = None) -> bytes:
        if report_type == "arabic":
            raise TypeError("Legacy generator cannot handle Arabic")
        # Simple valid PDF
        return (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length 43>>stream\n"
            b"BT /F1 12 Tf 100 700 Td (Legacy PDF - English) Tj ET\n"
            b"endstream\nendobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000056 00000 n \n"
            b"0000000110 00000 n \n0000000210 00000 n \n0000000270 00000 n \n"
            b"trailer<</Size 6/Root 1 0 R>>\n"
            b"startxref\n380\n%%EOF\n"
        )


# -----------------------------
# Arabic PDF generator (fallback)
# -----------------------------
class ArabicPDFGenerator:
    def __init__(self):
        self.font_manager = ArabicFontManager()
        self.font_name = self.font_manager.register_font()
        logger.info(f"✅ ArabicPDFGenerator ready with font: {self.font_name}")

    def generate(self, dto) -> bytes:
        """Generate a professional Arabic PDF using ReportLab."""
        try:
            from reportlab.lib.enums import TA_RIGHT
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        except ImportError as e:
            logger.error(f"ReportLab missing: {e}")
            return self._minimal_pdf(dto)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        story = []
        styles = getSampleStyleSheet()

        arabic_style = ParagraphStyle(
            "ArabicStyle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=14,
            alignment=TA_RIGHT,
            rightIndent=0,
            leftIndent=0,
            leading=20,
            wordWrap="CJK",
        )

        # Extract data from DTO (using getattr for safety)
        device_id = getattr(dto, "device_id", "N/A")
        status_raw = getattr(dto, "final_status", "safe")
        status_map = {"safe": "آمن", "warning": "تحذير", "rejected": "مرفوض"}
        logical_status = status_map.get(status_raw.lower(), status_raw)

        # Build content
        story.append(Paragraph("الحارس الرقمي", arabic_style))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("سلسلة التبريد", arabic_style))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"معرف الجهاز: {device_id}", arabic_style))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(f"الحالة: {logical_status}", arabic_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        logger.info(f"✅ Professional Arabic PDF generated: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def _minimal_pdf(self, dto) -> bytes:
        """Ultra-minimal valid PDF when ReportLab is missing."""
        device_id = getattr(dto, "device_id", "N/A")
        status_raw = getattr(dto, "final_status", "safe")
        status_map = {"safe": "آمن", "warning": "تحذير", "rejected": "مرفوض"}
        logical_status = status_map.get(status_raw.lower(), status_raw)

        pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 200>>stream
BT
/F1 20 Tf 100 750 Td (الحارس الرقمي) Tj
/F1 14 Tf 100 720 Td (سلسلة التبريد) Tj
/F1 12 Tf 100 690 Td (معرف الجهاز: {device_id}) Tj
100 670 Td (الحالة: {logical_status}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000056 00000 n
0000000110 00000 n
0000000210 00000 n
0000000270 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
450
%%EOF
"""
        return pdf.encode("utf-8")


# -----------------------------
# Main wrapper
# -----------------------------
class UnifiedPDFGeneratorWrapper:
    def __init__(self):
        self._legacy = LegacyPDFGenerator()
        self._arabic_gen = None
        # compatibility helpers used by older tests/integration
        self._inner = self._legacy
        self._unified = self._legacy
        logger.info("🚀 Wrapper initialized")

    def _ensure_initialized(self):
        """No-op shim; newer tests expect this method to exist."""
        return

    def _ensure_arabic_generator(self):
        if self._arabic_gen is None:
            self._arabic_gen = ArabicPDFGenerator()

    def _resolve_report_type(self, dto):
        status = getattr(dto, "final_status", "safe").lower()
        return "official" if status == "safe" else "technical"

    def render(self, dto, force_report_type: Optional[str] = None) -> bytes:
        is_arabic = force_report_type == "arabic"
        if is_arabic:
            logger.info("🇸🇦 Arabic forced – using Arabic generator")
            self._ensure_arabic_generator()
            return self._arabic_gen.generate(dto)

        # allow external test harnesses to disable the primary engine by
        # nulling out ``_inner``.  this is a backward-compatibility hack and is
        # not part of the normal public API.
        if getattr(self, "_inner", None) is None:
            logger.warning("fallback triggered because inner engine missing")
            self._ensure_arabic_generator()
            return self._arabic_gen.generate(dto)

        report_type = force_report_type or self._resolve_report_type(dto)
        try:
            return self._legacy.generate(report_type, data_path=None)
        except Exception as e:
            logger.warning(f"Legacy failed ({e}) – falling back to Arabic generator")
            self._ensure_arabic_generator()
            return self._arabic_gen.generate(dto)


# -----------------------------
# Singleton factory – EXPORT THIS
# -----------------------------
_wrapper_instance = None


def get_pdf_generator() -> UnifiedPDFGeneratorWrapper:
    global _wrapper_instance
    if _wrapper_instance is None:
        _wrapper_instance = UnifiedPDFGeneratorWrapper()
    return _wrapper_instance
