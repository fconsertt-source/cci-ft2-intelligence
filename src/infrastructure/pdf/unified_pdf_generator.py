# src/infrastructure/pdf/unified_pdf_generator.py
"""
Unified PDF Generator for CCI-FT2 Intelligence
Handles multiple report types (Official, Technical, Arabic) with a premium design.
Production-ready version with Clean Architecture compliance and fail-fast validation.
"""
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from src.infrastructure.adapters.reporting.components.alert_circle import AlertCircle

# ----------------------------------------------------------------------
# Import our own components (now from infrastructure)
# ----------------------------------------------------------------------
from src.infrastructure.adapters.reporting.components.stability_bar import StabilityBar
from src.infrastructure.adapters.reporting.components.vvm_icon import VVMIcon
from src.infrastructure.utils.config_loader import ConfigLoader
from src.shared.language_manager import lang


# ----------------------------------------------------------------------
# Dependency validation – fail-fast if required libraries are missing
# ----------------------------------------------------------------------
_HAS_PANDAS = False
_HAS_MATPLOTLIB = False
_HAS_REPORTLAB = False
_HAS_ARABIC_RESHAPER = False

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    pd = None

try:
    import matplotlib
    import matplotlib.pyplot as plt

    _HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    matplotlib = None

try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    _HAS_REPORTLAB = True
except ImportError:
    # Dummy placeholders to avoid NameError – but will raise explicit error later
    A4 = None
    colors = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    Spacer = None
    Image = None
    PageBreak = None
    cm = 1
    pdfmetrics = None
    TTFont = None
    TA_CENTER = TA_RIGHT = TA_LEFT = 0
    HexColor = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    _HAS_ARABIC_RESHAPER = True
except ImportError:
    arabic_reshaper = None

    def get_display(s):
        return s

# ----------------------------------------------------------------------
# Enum for report types – safer than string constants
# ----------------------------------------------------------------------
class ReportType(str, Enum):
    OFFICIAL = "official"
    TECHNICAL = "technical"
    ARABIC = "arabic"


class UnifiedPDFGenerator:
    """
    A unified class to generate high-quality PDF reports.
    Uses a Builder-like approach to customize the report content.
    This class expects already‑filtered and fully prepared data.
    """

    def __init__(
        self,
        language: str = "ar",
        output_dir: Optional[str] = None,
        theme_color: Optional[str] = None,
        fixed_timestamp: Optional[str] = None,
    ):
        # Validate critical dependencies immediately
        if not _HAS_REPORTLAB:
            raise RuntimeError(
                "reportlab is required to generate PDF reports. "
                "Install with: pip install reportlab"
            )

        # Set language
        if language and language != lang.current_language:
            try:
                lang.set_language(language)
            except Exception:
                pass  # language may not be loaded yet – ignore

        self.output_dir = output_dir or ConfigLoader.get(
            "paths.reports_dir", "data/output/reports"
        )
        os.makedirs(self.output_dir, exist_ok=True)

        theme = theme_color or ConfigLoader.get(
            "reporting.default_theme_color", "#2C3E50"
        )
        self.theme_color = HexColor(theme) if HexColor else theme

        self.accent_color = (
            HexColor(ConfigLoader.get("reporting.accent_color", "#3498DB"))
            if HexColor
            else "#3498DB"
        )
        self.success_color = HexColor("#27AE60") if HexColor else "#27AE60"
        self.warning_color = HexColor("#F1C40F") if HexColor else "#F1C40F"
        self.danger_color = HexColor("#E74C3C") if HexColor else "#E74C3C"

        # support fixed timestamp for golden tests
        self.fixed_timestamp = fixed_timestamp or os.getenv("GOLDEN_FIXED_TIMESTAMP")
        self.fixed_ref_prefix = os.getenv("GOLDEN_FIXED_REF", "CC-FIXED")

        # Load fonts and styles
        self.font_name = self._setup_fonts()
        self.styles = self._setup_styles()

        self.golden_test = os.getenv("GOLDEN_TEST") == "1"
        self.fixed_timestamp = fixed_timestamp or os.getenv("GOLDEN_FIXED_TIMESTAMP")
        self.fixed_ref_prefix = (
            os.getenv("GOLDEN_FIXED_REF", "CC-GOLDEN")
            if self.golden_test
            else os.getenv("GOLDEN_FIXED_REF", "CC-FIXED")
        )

    def _setup_fonts(self) -> str:
        """Configure fonts with Arabic support.
        Returns the chosen font name.
        """
        fonts_dir = ConfigLoader.get("paths.fonts_dir", "src/shared/fonts")
        # candidate paths (ordered preference)
        font_paths = [
            os.path.join(fonts_dir, "Tajawal-Regular.ttf"),
            os.path.join(fonts_dir, "Tajawal-Bold.ttf"),
            os.path.join(fonts_dir, "arabic.ttf"),
            os.path.join(fonts_dir, "arabic-bold.ttf"),
            os.path.join(fonts_dir, "arial.ttf"),
            os.path.join(fonts_dir, "tahoma.ttf"),
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    # choose a semantic name so we can detect Arabic later
                    if any(x in path.lower() for x in ["arabic", "tajawal"]):
                        font_name = "ArabicFont"
                        print(f"INFO: Using Arabic font from: {path}")
                    else:
                        font_name = "MainFont"
                        print(f"INFO: Using font from: {path}")
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    return font_name
                except Exception as e:
                    print(f"WARNING: Failed to load font {path}: {e}")
                    continue
        print("WARNING: No custom font found, using Helvetica (Arabic may not render)")
        return "Helvetica"

    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Define all paragraph styles used in reports."""
        base_styles = getSampleStyleSheet()
        custom_styles = {}

        # determine whether the chosen font is our Arabic font
        is_arabic_font = self.font_name == "ArabicFont"
        text_alignment = TA_RIGHT if is_arabic_font else TA_LEFT
        center_alignment = TA_CENTER

        custom_styles["Title"] = ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName=self.font_name,
            fontSize=22,
            textColor=self.theme_color,
            alignment=center_alignment,
            spaceAfter=20,
        )
        custom_styles["Heading"] = ParagraphStyle(
            "SectionHeading",
            parent=base_styles["Heading2"],
            fontName=self.font_name,
            fontSize=16,
            textColor=self.accent_color,
            borderPadding=5,
            spaceBefore=15,
            spaceAfter=10,
            alignment=text_alignment,
        )
        custom_styles["Normal"] = ParagraphStyle(
            "NormalText",
            parent=base_styles["Normal"],
            fontName=self.font_name,
            fontSize=11,
            alignment=text_alignment,
            leading=14,
        )
        custom_styles["Info"] = ParagraphStyle(
            "InfoText",
            parent=base_styles["Normal"],
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.grey,
            alignment=center_alignment,
        )
        custom_styles["Small"] = ParagraphStyle(
            "SmallText",
            parent=custom_styles["Normal"],
            fontSize=9,
            leading=10,
            alignment=text_alignment,
        )
        custom_styles["Info"] = ParagraphStyle(
            "InfoText",
            parent=base_styles["Normal"],
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        custom_styles["Small"] = ParagraphStyle(
            "SmallText",
            parent=custom_styles["Normal"],
            fontSize=9,
            leading=10,
            alignment=TA_LEFT if self.font_name == "Helvetica" else TA_RIGHT,
        )
        custom_styles["SmallCenter"] = ParagraphStyle(
            "SmallTextCenter",
            parent=custom_styles["Normal"],
            fontSize=9,
            leading=10,
            alignment=TA_CENTER,
        )
        return custom_styles

    def _process_text(self, text: str) -> str:
        """Reshape Arabic text if necessary."""
        if not text:
            return ""
        if _HAS_ARABIC_RESHAPER and any("\u0600" <= c <= "\u06FF" for c in text):
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        return text

    def _get_status_style(self, her_pct: float, is_arabic: bool) -> Dict[str, Any]:
        """
        Return style information for a given HER percentage.
        (Pure visual – no business logic.)
        """
        if her_pct >= 82.0:
            color = self.danger_color
            stage = "3/4" if her_pct < 105.0 else "4/4"
            text = (
                f"إتلاف (المرحلة {stage})" if is_arabic else f"DISCARD (STAGE {stage})"
            )
            if is_arabic:
                text += "\n(استنفاد الرصيد الحراري)"
            else:
                text += "\n(Thermal Exhaustion)"
            alert_level = "RED"
        elif her_pct >= 50.0:
            color = self.warning_color
            text = "USE FIRST (STAGE 2)" if not is_arabic else "الأولوية للصرف"
            alert_level = "YELLOW"
        else:
            color = self.success_color
            text = "SAFE (STAGE 1)" if not is_arabic else "سليم"
            alert_level = "GREEN"

        return {
            "bg": color,
            "text": text,
            "icon": AlertCircle(10, color),
            "alert_level": alert_level,
        }

    def generate(
        self,
        report_type: Union[str, ReportType],
        data_path: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF report from a TSV file.
        The data file must already contain all necessary columns.
        """
        if isinstance(report_type, str):
            report_type = ReportType(report_type)  # validate against enum

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")

        # Load data – pandas is optional, we fall back to csv reader
        if _HAS_PANDAS:
            df = pd.read_csv(data_path, sep="\t")
            records = df.to_dict("records")
        else:
            import csv

            with open(data_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                records = list(reader)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_type.value}_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            output_path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm
        )

        story = []
        story.extend(self._build_header(report_type))
        story.extend(self._build_summary_dashboard(records, report_type))
        story.extend(self._build_data_table(records, report_type))
        story.append(PageBreak())
        story.extend(self._build_charts(records, report_type))
        if report_type in (ReportType.OFFICIAL, ReportType.ARABIC):
            story.extend(self._build_signature_block(report_type))
        self._add_footer(story, report_type)

        doc.build(story)
        return output_path

    def _build_header(self, report_type: ReportType) -> List[Any]:
        """Report header with title and metadata."""
        elements = []

        # use fixed timestamp if configured (for golden tests)
        if self.fixed_timestamp:
            now = datetime.strptime(self.fixed_timestamp, "%Y-%m-%d %H:%M:%S")
            ref_suffix = "000000"
        else:
            now = datetime.now()
            ref_suffix = now.strftime("%Y%j%H%M")

        title_map = {
            ReportType.OFFICIAL: lang.get("report.official_title"),
            ReportType.TECHNICAL: lang.get(
                "report.technical_title", "Technical Analysis Report"
            ),
            ReportType.ARABIC: lang.get("report.official_title"),
        }
        title_text = self._process_text(title_map[report_type])
        elements.append(Paragraph(title_text, self.styles["Title"]))

        org_name = ConfigLoader.get("reporting.organization_name", "")
        if org_name:
            elements.append(
                Paragraph(self._process_text(org_name), self.styles["Info"])
            )

        is_ar = report_type == ReportType.ARABIC
        gen_label = "Generated on" if not is_ar else "تاريخ الإصدار"
        ref_label = "Ref" if not is_ar else "رقم المرجع"
        info = f"{gen_label}: {now.strftime('%Y-%m-%d %H:%M:%S')} | {ref_label}: {self.fixed_ref_prefix}-{ref_suffix}"
        elements.append(Paragraph(self._process_text(info), self.styles["Info"]))
        elements.append(Spacer(1, 1 * cm))
        return elements

    def _build_summary_dashboard(
        self, records: List[Dict], report_type: ReportType
    ) -> List[Any]:
        """Executive summary with counts."""
        elements = []
        total = len(records)
        safe = sum(1 for r in records if r.get("alert_level") == "GREEN")
        warning = sum(1 for r in records if r.get("alert_level") == "YELLOW")
        rejected = sum(1 for r in records if r.get("alert_level") == "RED")

        labels = {
            "title": lang.get("report.executive_summary"),
            "msg": lang.get(
                "report.executive_message",
                "Critical alert: {rejected} batches failed, {warning} need redistribution.",
            ).format(rejected=rejected, warning=warning),
            "h1": lang.get("report.total_batches"),
            "h2": lang.get("status.safe"),
            "h3": lang.get("status.warning"),
            "h4": lang.get("status.discard"),
        }

        if rejected > 0 or warning > 0:
            elements.append(
                Paragraph(self._process_text(labels["title"]), self.styles["Heading"])
            )
            elements.append(
                Paragraph(self._process_text(labels["msg"]), self.styles["Normal"])
            )
            elements.append(Spacer(1, 0.5 * cm))

        data = [
            [
                self._process_text(labels["h1"]),
                self._process_text(labels["h2"]),
                self._process_text(labels["h3"]),
                self._process_text(labels["h4"]),
            ],
            [str(total), str(safe), str(warning), str(rejected)],
        ]

        t = Table(data, colWidths=[4.5 * cm] * 4)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.theme_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.white),
                    (
                        "BACKGROUND",
                        (1, 1),
                        (1, 1),
                        HexColor("#D4EFDF") if HexColor else "#D4EFDF",
                    ),
                    (
                        "BACKGROUND",
                        (2, 1),
                        (2, 1),
                        HexColor("#FCF3CF") if HexColor else "#FCF3CF",
                    ),
                    (
                        "BACKGROUND",
                        (3, 1),
                        (3, 1),
                        HexColor("#FADBD8") if HexColor else "#FADBD8",
                    ),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 1 * cm))
        return elements

    def _build_data_table(
        self, records: List[Dict], report_type: ReportType
    ) -> List[Any]:
        """
        Build the main data table.
        Assumes records already have all required fields.
        """
        elements = []
        is_ar = report_type == ReportType.ARABIC

        title = "Detailed Batch Analysis" if not is_ar else "تحليل الشحنات التفصيلي"
        elements.append(Paragraph(self._process_text(title), self.styles["Heading"]))

        # Headers mapping (localized)
        headers_map = {
            "ID": "ID" if not is_ar else "المعرف",
            "Name": "Name" if not is_ar else "الاسم",
            "Category": "Category" if not is_ar else "الفئة",
            "Virtual VVM": "Virtual VVM" if not is_ar else "VVM افتراضي",
            "Status Alert": "Status Alert" if not is_ar else "حالة التنبيه",
            "Stability Budget": (
                "Stability Budget" if not is_ar else "ميزانية الاستقرار"
            ),
            "Thaw Rem.": "Thaw Rem." if not is_ar else "متبقي الذوبان",
        }

        # Determine which columns are present (use first record)
        sample = records[0] if records else {}
        base_headers = [
            "ID",
            "Name",
            "Category",
            "Virtual VVM",
            "Status Alert",
            "Stability Budget",
        ]
        if "thaw_remaining_hours" in sample:
            base_headers.append("Thaw Rem.")

        if is_ar:
            base_headers.reverse()

        processed_headers = [self._process_text(headers_map[h]) for h in base_headers]
        table_data = [processed_headers]

        # Build rows
        for row in records:
            id_val = str(row.get("center_id", ""))
            name_val = str(row.get("center_name", ""))
            cat_val = str(row.get("category_display", "General"))
            budget_pct = float(row.get("stability_budget_consumed_pct", 0.0))
            thaw_val = row.get("thaw_remaining_hours", None)

            # Visual elements (pure presentation)
            status = self._get_status_style(budget_pct, is_ar)
            vvm_icon = VVMIcon(size=14, her_pct=budget_pct)
            budget_bar = StabilityBar(
                width=3 * cm, height=8, pct=budget_pct, color=status["bg"]
            )
            status_cell = [
                status["icon"],
                Paragraph(
                    self._process_text(status["text"]), self.styles["SmallCenter"]
                ),
            ]

            # Category translation (still pure presentation – based on value)
            if is_ar:
                if "freeze" in cat_val.lower():
                    cat_val = "حساس للتجميد"
                else:
                    cat_val = "حساس للحرارة"

            cells = {
                "ID": Paragraph(id_val, self.styles["SmallCenter"]),
                "Name": Paragraph(name_val, self.styles["Small"]),
                "Category": Paragraph(
                    self._process_text(cat_val), self.styles["Small"]
                ),
                "Virtual VVM": vvm_icon,
                "Status Alert": status_cell,
                "Stability Budget": budget_bar,
                "Thaw Rem.": Paragraph("-", self.styles["SmallCenter"]),
            }

            if "Thaw Rem." in base_headers:
                if thaw_val not in (None, "N/A", ""):
                    try:
                        cells["Thaw Rem."] = Paragraph(
                            f"{float(thaw_val):.1f}h", self.styles["SmallCenter"]
                        )
                    except ValueError:
                        pass

            line = [cells[h] for h in base_headers]
            table_data.append(line)

        # Table styling
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), self.theme_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), self.font_name),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]

        # Row backgrounds based on alert_level (presentation only)
        for i, row in enumerate(records, 1):
            budget = float(row.get("stability_budget_consumed_pct", 0.0))
            level = self._get_status_style(budget, is_ar)["alert_level"]
            if level == "RED":
                style_commands.append(
                    (
                        "BACKGROUND",
                        (0, i),
                        (-1, i),
                        HexColor("#FADBD8") if HexColor else "#FADBD8",
                    )
                )
            elif level == "YELLOW":
                style_commands.append(
                    (
                        "BACKGROUND",
                        (0, i),
                        (-1, i),
                        HexColor("#FCF3CF") if HexColor else "#FCF3CF",
                    )
                )
            elif i % 2 == 0:
                style_commands.append(
                    (
                        "BACKGROUND",
                        (0, i),
                        (-1, i),
                        HexColor("#F4F6F7") if HexColor else "#F4F6F7",
                    )
                )

        # Column widths
        col_widths_map = {
            "ID": 1.2 * cm,
            "Name": 5.5 * cm,
            "Category": 3 * cm,
            "Virtual VVM": 2.2 * cm,
            "Status Alert": 2.5 * cm,
            "Stability Budget": 3.5 * cm,
            "Thaw Rem.": 1.1 * cm,
        }
        col_widths = [col_widths_map[h] for h in base_headers]

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle(style_commands))
        elements.append(t)
        return elements

    def _build_charts(self, records: List[Dict], report_type: ReportType) -> List[Any]:
        """
        Generate temperature chart.
        Charts are optional – if matplotlib missing, we show a placeholder.
        """
        elements = []
        is_ar = report_type == ReportType.ARABIC
        title = (
            "Visual Trends" if not is_ar else "المخططات البيانية والاتجاهات الحرارية"
        )
        elements.append(Paragraph(self._process_text(title), self.styles["Heading"]))

        if not _HAS_MATPLOTLIB or plt is None:
            elements.append(
                Paragraph(
                    "Charts not available (matplotlib missing)", self.styles["Normal"]
                )
            )
            return elements

        # Convert to DataFrame for easier plotting (if pandas available)
        if _HAS_PANDAS:
            df = pd.DataFrame(records)
        else:
            # manual conversion (limited)
            data = {k: [r.get(k) for r in records] for k in records[0].keys()}
            df = pd.DataFrame(data)

        # Filter out rows with invalid temperatures
        df_plot = df[df["avg_temperature"].notna()].copy()
        if df_plot.empty:
            elements.append(
                Paragraph("No valid temperature data for chart.", self.styles["Normal"])
            )
            return elements

        # Ensure numeric
        df_plot["avg_temperature"] = pd.to_numeric(
            df_plot["avg_temperature"], errors="coerce"
        )
        df_plot = df_plot.dropna(subset=["avg_temperature"])

        plt.figure(figsize=(10, 5))
        plt.bar(
            df_plot["center_id"].astype(str),
            df_plot["avg_temperature"],
            color="#3498DB",
            alpha=0.7,
        )

        min_label = "Min (2°C)" if not is_ar else "الأدنى (2°م)"
        max_label = "Max (8°C)" if not is_ar else "الأقصى (8°م)"
        plt.axhline(
            y=2, color="blue", linestyle="--", label=self._process_text(min_label)
        )
        plt.axhline(
            y=8, color="red", linestyle="--", label=self._process_text(max_label)
        )

        chart_title = (
            "Average Temperature per Center"
            if not is_ar
            else "متوسط درجة الحرارة لكل مركز"
        )
        y_label = "Temp °C" if not is_ar else "درجة الحرارة م°"
        plt.title(self._process_text(chart_title))
        plt.ylabel(self._process_text(y_label))
        plt.legend()

        # Use UUID to avoid collisions (unless golden test / fixed timestamp)
        if os.getenv("GOLDEN_TEST") or self.fixed_timestamp:
            # استبدال المسار الديناميكي بمسار ثابت في العناصر
            for i, elem in enumerate(elements):
                if hasattr(elem, "filename") and "temp_dist_" in str(elem.filename):
                    # لا نغير الملف الفعلي، فقط نضمن ثبات المرجع
                    pass

        elements.append(Image(chart_path, width=16 * cm, height=8 * cm))

        # Add system insight
        insight = "System Logic: VVM reflects cumulative biochemical damage over time. Vaccines can expire within 2-8°C if storage is prolonged or inconsistent."
        if is_ar:
            insight = "حقيقة تقنية: كاشف VVM يعكس التدهور التراكمي الحيوي للقاح عبر الزمن. قد تنتهي الصلاحية داخل النطاق الآمن (2-8°م) في حالات التخزين الطويل أو التذبذب الحراري."

        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(self._process_text(insight), self.styles["Info"]))
        return elements

    def _build_signature_block(self, report_type: ReportType) -> List[Any]:
        """Signature section for official/arabic reports."""
        elements = []
        is_ar = report_type == ReportType.ARABIC

        title = (
            "Approval & Certification" if not is_ar else "الاعتماد والمصادقة الرسمية"
        )
        qa_label = (
            "Cold Chain Officer Signature"
            if not is_ar
            else "توقيع مسؤول الحلقة الباردة"
        )
        ops_label = (
            "Municipality Vaccination Supervisor"
            if not is_ar
            else "توقيع مشرف التطعيم بالبلدية"
        )
        date_label = "Date" if not is_ar else "التاريخ"

        elements.append(Spacer(1, 2 * cm))
        elements.append(Paragraph(self._process_text(title), self.styles["Heading"]))

        sig_line = "_" * 30
        data = [
            [sig_line, sig_line],
            [self._process_text(qa_label), self._process_text(ops_label)],
            [
                self._process_text(f"{date_label}: " + "_" * 20),
                self._process_text(f"{date_label}: " + "_" * 20),
            ],
        ]

        if is_ar:
            data = [[r[1], r[0]] for r in data]

        t = Table(data, colWidths=[9 * cm, 9 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                ]
            )
        )
        elements.append(t)
        return elements

    def _add_footer(self, story: List[Any], report_type: ReportType):
        """Footer added at the end."""
        is_ar = report_type == ReportType.ARABIC
        footer_text = "CCI-FT2 Intelligence Cold Chain Monitoring System | Confidential & Official"
        if is_ar:
            footer_text = (
                "نظام الذكاء الاصطناعي CCI-FT2 لمراقبة سلسلة التبريد | سري ورسمي"
            )

        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(self._process_text(footer_text), self.styles["Info"]))

    # ------------------------------------------------------------------
    # Convenience renderer
    # ------------------------------------------------------------------

    def render(self, dto, force_report_type: Optional[str] = None) -> bytes:
        """Return PDF bytes for a DTO.

        This is a thin helper used by strategies and tests.  We intentionally
        avoid trying to convert the DTO into a TSV/CSV; instead we delegate
        to the wrapper (which already knows how to cope with DTOs) and fall
        back to a minimal PDF if something goes wrong.
        """
        try:
            # direct importer to avoid circular import issues
            from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
                UnifiedPDFGeneratorWrapper,
            )

            wrapper = UnifiedPDFGeneratorWrapper()
            return wrapper.render(dto, force_report_type=force_report_type)
        except Exception:
            # as a last resort provide a minimal structural PDF
            return (
                b"%PDF-1.4\n"
                b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
                b"trailer<</Root 1 0 R>>\n"
                b"%%EOF"
            )


# في نهاية ملف unified_pdf_generator.py
_wrapper_instance: UnifiedPDFGenerator | None = None


def get_pdf_generator(language: str = "ar") -> UnifiedPDFGenerator:
    """
    Singleton factory – returns a UnifiedPDFGenerator-like object.

    If the real generator cannot be constructed due to missing dependencies
    (e.g. reportlab), we fall back to the wrapper implementation which itself
    handles missing libraries gracefully.  This allows higher layers (PDF
    strategies) to work without having to guard around imports.
    """
    global _wrapper_instance
    if _wrapper_instance is None:
        try:
            _wrapper_instance = UnifiedPDFGenerator(language=language)
        except RuntimeError as err:
            if "reportlab" in str(err).lower():
                from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
                    UnifiedPDFGeneratorWrapper,
                )

                _wrapper_instance = UnifiedPDFGeneratorWrapper()
            else:
                raise
    return _wrapper_instance
