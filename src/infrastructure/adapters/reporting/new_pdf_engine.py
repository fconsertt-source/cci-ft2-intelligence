# src/infrastructure/adapters/reporting/new_pdf_engine.py
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

from src.infrastructure.logging import get_logger
from src.presentation.reporting.components.header_builder import (
    FooterBuilder, HeaderBuilder)

logger = get_logger(__name__)


def register_arabic_fonts():
    """تصدير للتوافق مع golden test"""
    try:
        font_path = Path("assets/fonts/NotoSansArabic-Regular.ttf")
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("NotoSans", str(font_path)))
            return "NotoSans"
    except Exception:
        pass
    return "Helvetica"


class PDFGenerator:
    def __init__(self, language: str = "ar", theme_color: str = "blue") -> None:
        self.language = language
        self.theme_color = theme_color
        self.font_name = register_arabic_fonts()

    def generate(
        self,
        dto: Any,
        report_type: str = "official",
        language: Optional[str] = None,
    ) -> bytes:
        lang = language or self.language
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        hb = HeaderBuilder(self.font_name, styles)
        elements.extend(hb.build(report_type, dto, language=lang))
        elements.append(Spacer(1, 20))

        # بناء الجدول بالأعمدة الدقيقة من الصورة
        daily_map = defaultdict(list)
        for entry in getattr(dto, "readings", []):
            d_key = entry.timestamp.date()
            daily_map[d_key].append(entry)

        table_data = [
            [
                "Date",
                "Avg temp.\n(°C)",
                "Status",
                "Min. temp.\n(°C)",
                "Cumulative\ndaily time\nbelow",
                "Alarm\ntrigger\ntime",
                "Max. temp.\n(°C)",
                "Cumulative\ndaily time\nabove",
            ]
        ]

        for d in sorted(daily_map.keys()):
            entries = daily_map[d]
            min_t = max_t = avg_t = None
            dur_low = dur_high = 0
            status = "OK"

            for e in entries:
                meta = getattr(e, "meta", "") or ""
                tag = meta.split("|")[0] if "|" in meta else ""
                stat = meta.split("|")[1] if "|" in meta else "OK"
                if stat != "OK":
                    status = stat

                if "FT2_MIN" in tag:
                    min_t = e.temperature
                    dur_low = int(e.duration_minutes)
                elif "FT2_MAX" in tag:
                    max_t = e.temperature
                    dur_high = int(e.duration_minutes)
                elif "FT2_AVG" in tag:
                    avg_t = e.temperature

            row = [
                d.strftime("%d.%m.%Y"),
                f"{avg_t:.1f}" if avg_t is not None else "-",
                status,
                f"{min_t:.1f}" if min_t is not None else "-",
                f"{dur_low//60:02d}:{dur_low%60:02d}",
                "-",
                f"{max_t:.1f}" if max_t is not None else "-",
                f"{dur_high//60:02d}:{dur_high%60:02d}",
            ]
            table_data.append(row)

        t = Table(table_data, colWidths=[60, 45, 40, 45, 65, 50, 45, 65])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )

        # تلوين الخلايا الحمراء
        for i, row in enumerate(table_data[1:], 1):
            if row[2] != "OK":
                t.setStyle(TableStyle([("TEXTCOLOR", (2, i), (2, i), colors.red)]))
            if row[4] != "00:00":
                t.setStyle(TableStyle([("TEXTCOLOR", (4, i), (4, i), colors.red)]))
            if row[7] != "00:00":
                t.setStyle(TableStyle([("TEXTCOLOR", (7, i), (7, i), colors.red)]))

        elements.append(t)

        fb = FooterBuilder(self.font_name, styles)
        elements.extend(fb.build(dto))

        doc.build(elements)
        return buffer.getvalue()
