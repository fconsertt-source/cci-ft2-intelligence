# src/infrastructure/adapters/reporting/new_pdf_engine.py

"""Modular replacement for UnifiedPDFGenerator.

This file defines a new `PDFGenerator` class with a simple public API:

    generator = PDFGenerator()
    pdf_bytes = generator.generate(dto, report_type="official", language="ar")

Internally it will delegate to builder components located in
`src/presentation/reporting/components`.

The implementation is currently a stub; the legacy engine remains available
until migration completes.
"""

import sys
from pathlib import Path
from typing import Any, Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ✅ Add logging
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Helper to ensure all story elements are Flowables
try:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Flowable, Paragraph
except ImportError:
    Paragraph = None  # type: ignore
    Flowable = None  # type: ignore
    ParagraphStyle = Any  # type: ignore


def register_arabic_fonts():
    """تسجيل خط Amiri العربي في ReportLab مع مسارات مرنة"""
    # قائمة المسارات المحتملة
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent
        / "assets/fonts/Amiri-Regular.ttf",
        Path(__file__).parent.parent.parent / "assets/fonts/Amiri-Regular.ttf",
        Path("assets/fonts/Amiri-Regular.ttf"),
    ]

    font_path = None
    for p in possible_paths:
        if p.exists():
            font_path = p
            break

    if font_path is None:
        raise FileNotFoundError(
            f"Amiri font not found in any expected location: {possible_paths}"
        )

    pdfmetrics.registerFont(TTFont("Amiri", str(font_path)))

    # تسجيل النسخة العريضة إذا موجودة
    bold_path = font_path.parent / "Amiri-Bold.ttf"
    if bold_path.exists():
        pdfmetrics.registerFont(TTFont("Amiri-Bold", str(bold_path)))


def ensure_flowable(obj: Any, style: Any) -> Any:
    """
    تأكد أن العنصر المرسل إلى story هو Flowable صالح.
    - إذا كان Flowable بالفعل، إرجاعه كما هو.
    - إذا كان str، تحويله إلى Paragraph باستخدام style.
    - أي شيء آخر، تحويله إلى str ثم Paragraph.
    """
    if Flowable and isinstance(obj, Flowable):
        return obj
    if Paragraph:
        if isinstance(obj, str):
            return Paragraph(obj, style)
        return Paragraph(str(obj), style)
    return obj


class PDFGenerator:
    def __init__(self, language: str = "ar", theme_color: str = "blue") -> None:
        # future: load fonts, set up styles, ensure dependencies
        self.language = language
        # basic theme configuration used by chart builder etc.
        self.theme_color = theme_color
        # determine base font name (may register Arabic-capable font if needed)
        self.font_name = "Helvetica"
        if self.language == "ar":
            try:
                # reuse wrapper's font registration logic to avoid duplication
                from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
                    _register_arabic_font,
                )

                self.font_name = _register_arabic_font()
            except Exception:
                # if registration fails, fall back to generic font
                self.font_name = "Helvetica"

    def generate(
        self,
        dto: Any,
        report_type: str = "official",
        language: Optional[str] = None,
    ) -> bytes:
        """Return PDF bytes for supplied DTO.

        The implementation will eventually replace
        `UnifiedPDFGeneratorWrapper` as the default generator.
        """
        # attempt to build a real PDF using reportlab and the new component
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.platypus import SimpleDocTemplate

        from src.presentation.reporting.components.arabic_processor import shape
        from src.presentation.reporting.components.chart_builder import ChartBuilder

        # import our builders
        from src.presentation.reporting.components.header_builder import (
            FooterBuilder,
            HeaderBuilder,
        )
        from src.presentation.reporting.components.table_builder import TableBuilder

        # determine language for this run
        if language is not None:
            lang = language
        else:
            lang = self.language

        # build document story
        from io import BytesIO

        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Spacer

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # assemble paragraph styles; we start with a sample stylesheet and
        # override font names if Arabic.
        styles = getSampleStyleSheet()
        if lang == "ar":
            for key in ("Title", "Normal", "Info"):  # some keys may not exist
                if key in styles:
                    styles[key].fontName = self.font_name
        # let builders receive both font and styles
        hb = HeaderBuilder(self.font_name, styles)
        fb = FooterBuilder(self.font_name, styles)
        tb = TableBuilder(self.font_name, styles)
        cb = ChartBuilder(self.theme_color)

        # header
        elements.extend(hb.build(report_type, dto, language=lang))
        # dummy body from dto (perhaps scientific_rationale)
        body = getattr(dto, "scientific_rationale", "")
        if lang == "ar":
            body = shape(body)
        if body:
            # convert to Paragraph to ensure it's a valid flowable
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import Paragraph

            base_style = getSampleStyleSheet()["Normal"]
            body_style = ParagraphStyle(
                "BodyText", parent=base_style, fontName=self.font_name, alignment=1
            )
            elements.append(Paragraph(body, body_style))
            elements.append(Spacer(1, 12))

            elements.append(Spacer(1, 12))

        # example table + chart
        records = []
        elements.extend(tb.build(records, report_type))
        elements.extend(cb.build(records, report_type))

        # footer
        elements.extend(fb.build(dto))

        # Sanitize elements to ensure they are all Flowables
        normal_style = styles.get("Normal")
        if normal_style is None:
            from reportlab.lib.styles import getSampleStyleSheet

            normal_style = getSampleStyleSheet()["Normal"]

        elements = [ensure_flowable(e, normal_style) for e in elements]

        try:
            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            # sometimes ReportLab builds a valid PDF with no pages (Count 0)
            # which isn't useful; detect and treat it as failure so we fall back.
            if b"/Type /Page" not in pdf_bytes:
                raise ValueError("generated PDF contained no pages")

            return pdf_bytes
        except Exception as e:
            # if building fails or produced empty document, log and re-raise.
            # This ensures that tests fail loudly instead of passing with a
            # minimal (and incorrect) PDF.
            logger.exception("ReportLab generation failed")
            # ⚠️ في الاختبارات لا يجب الرجوع إلى minimal
            raise
