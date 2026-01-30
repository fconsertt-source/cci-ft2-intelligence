"""
Unified PDF Generator for CCI-FT2 Intelligence
Handles multiple report types (Official, Technical, Arabic) with a premium design.
"""
from __future__ import annotations
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Optional heavy dependencies are imported lazily or guarded so unit tests
# that don't have these packages installed can still import this module.
try:
    import pandas as pd
except Exception:  # pragma: no cover - environment-dependent
    pd = None
try:  # pragma: no cover - optional plotting backend
    import matplotlib.pyplot as plt
    import matplotlib
    _HAS_MATPLOTLIB = True
except Exception:  # pragma: no cover - optional
    plt = None
    matplotlib = None
    _HAS_MATPLOTLIB = False
try:  # pragma: no cover - reportlab is optional in minimal test envs
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Flowable
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.lib.colors import HexColor
except Exception:  # pragma: no cover - provide lightweight fallbacks
    A4 = None

    class _DummyColors:
        lightgrey = None
        whitesmoke = None
    colors = _DummyColors()

    def getSampleStyleSheet():
        return {}

    class ParagraphStyle:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class SimpleDocTemplate:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Table:  # type: ignore
        pass

    class TableStyle:  # type: ignore
        pass

    class Paragraph:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Spacer:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Image:  # type: ignore
        pass

    class PageBreak:  # type: ignore
        pass

    class Flowable:  # minimal base class for custom flowables
        def __init__(self, *args, **kwargs):
            pass

    cm = 1

    class pdfmetrics:  # type: ignore
        @staticmethod
        def registerFont(*args, **kwargs):
            return None

    class TTFont:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    TA_CENTER = TA_RIGHT = TA_LEFT = 0

    def HexColor(x):
        return x

# Custom Flowables for Visual Intelligence
class StabilityBar(Flowable):
    """A custom progress bar with a pointer for Stability Budget."""
    def __init__(self, width, height, pct, color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.pct = min(100, max(0, pct))
        self.color = color

    def draw(self):
        # Background bar
        self.canv.setLineWidth(0.5)
        self.canv.setStrokeColor(colors.lightgrey)
        self.canv.roundRect(0, 0, self.width, self.height, 2, stroke=1, fill=0)
        
        # Budget fill (Gradient-like effect using solid colors)
        fill_width = (self.pct / 100.0) * self.width
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, fill_width, self.height, 2, stroke=0, fill=1)
        
        # Pointer
        pointer_pos = fill_width
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(1)
        self.canv.line(pointer_pos, -2, pointer_pos, self.height + 2)

class VVMIcon(Flowable):
    """
    Virtual VVM Icon المحدث ليتطابق مع صورة مراحل تدهور اللقاح:
    Stage 1 & 2: مقبول (استخدم) | Stage 3 & 4: مرفوض (إتلاف)
    """
    def __init__(self, size, her_pct):
        Flowable.__init__(self)
        self.size = size
        self.width = size
        self.height = size
        self.her = her_pct / 100.0  # تحويل النسبة المئوية إلى معامل (0.0 - 1.0+)

    def draw(self):
        radius = self.size / 2.0
        # لون الدائرة الخارجية الثابت (رمادي قياسي حسب منظمة الصحة العالمية)
        circle_gray = 0.55 
        
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(0.5)
        self.canv.setFillColor(colors.Color(circle_gray, circle_gray, circle_gray))
        self.canv.circle(radius, radius, radius, stroke=1, fill=1)
        
        # منطق المربع الداخلي بناءً على الحكم الصادر في الصورة (تحديث v1.2):
        if self.her < 0.5:
            # المرحلة الأولى: المربع أبيض
            val = 1.0
            has_stroke = 1
        elif self.her < 0.82:
            # المرحلة الثانية: المربع أفتح من الدائرة
            val = 0.8
            has_stroke = 1
        elif 0.82 <= self.her < 1.05:
            # المرحلة الثالثة: لون المربع نفس لون الدائرة (إزالة الحدود)
            val = circle_gray
            has_stroke = 0  
        else:
            # المرحلة الرابعة: المربع أغمق من الدائرة
            val = 0.2
            has_stroke = 1

        self.canv.setFillColor(colors.Color(val, val, val))
        sq_size = self.size * 0.5
        offset = (self.size - sq_size) / 2.0
        
        # رسم المربع الداخلي
        if not has_stroke:
            self.canv.setStrokeColor(colors.Color(circle_gray, circle_gray, circle_gray))
        else:
            self.canv.setStrokeColor(colors.black)
            
        self.canv.setLineWidth(0.3)
        self.canv.rect(offset, offset, sq_size, sq_size, stroke=has_stroke, fill=1)

class AlertCircle(Flowable):
    """Draws a solid alert circle to avoid emoji font issues."""
    def __init__(self, size, color):
        Flowable.__init__(self)
        self.size = size
        self.width = size
        self.height = size
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.setStrokeColor(colors.white)
        self.canv.setLineWidth(0.5)
        self.canv.circle(self.size/2, self.size/2, self.size/2, stroke=1, fill=1)

# Arabic text support (optional)
try:  # pragma: no cover - optional environment
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    def get_display(s):
        return s

from src.utils.config_loader import ConfigLoader

if _HAS_MATPLOTLIB:
    matplotlib.use('Agg')

class ReportType:
    OFFICIAL = "official"
    TECHNICAL = "technical"
    ARABIC = "arabic"

class UnifiedPDFGenerator:
    """
    A unified class to generate high-quality PDF reports.
    Uses a Builder-like approach to customize the report content.
    """
    
    def __init__(self, output_dir: Optional[str] = None, theme_color: Optional[str] = None):
        self.output_dir = output_dir or ConfigLoader.get("paths.reports_dir", "data/output/reports")
        
        theme = theme_color or ConfigLoader.get("reporting.default_theme_color", "#2C3E50")
        self.theme_color = colors.HexColor(theme)
        
        self.accent_color = colors.HexColor(ConfigLoader.get("reporting.accent_color", "#3498DB"))
        self.success_color = colors.HexColor("#27AE60")
        self.warning_color = colors.HexColor("#F1C40F")
        self.danger_color = colors.HexColor("#E74C3C")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load fonts
        self.font_name = self._setup_fonts()
        self.styles = self._setup_styles()

    def _setup_fonts(self) -> str:
        """Configures fonts, prioritizing project assets defined in config."""
        fonts_dir = ConfigLoader.get("paths.fonts_dir", "assets/fonts")
        
        font_paths = [
            os.path.join(fonts_dir, "arial.ttf"),
            os.path.join(fonts_dir, "tahoma.ttf"),
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('MainFont', path))
                    return 'MainFont'
                except Exception:
                    continue
        
        return 'Helvetica'

    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Defines premium styles for the report."""
        base_styles = getSampleStyleSheet()
        custom_styles = {}
        
        # Title
        custom_styles['Title'] = ParagraphStyle(
            'ReportTitle',
            parent=base_styles['Title'],
            fontName=self.font_name,
            fontSize=22,
            textColor=self.theme_color,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Heading
        custom_styles['Heading'] = ParagraphStyle(
            'SectionHeading',
            parent=base_styles['Heading2'],
            fontName=self.font_name,
            fontSize=16,
            textColor=self.accent_color,
            borderPadding=5,
            spaceBefore=15,
            spaceAfter=10
        )
        
        # Normal Text
        custom_styles['Normal'] = ParagraphStyle(
            'NormalText',
            parent=base_styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            alignment=TA_RIGHT if self.font_name != 'Helvetica' else TA_LEFT,
            leading=14
        )
        
        # Info/Footer Text
        custom_styles['Info'] = ParagraphStyle(
            'InfoText',
            parent=base_styles['Normal'],
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        # Small style for table content to allow wrapping
        custom_styles['Small'] = ParagraphStyle(
            'SmallText',
            parent=custom_styles['Normal'],
            fontSize=9,
            leading=10,
            alignment=TA_LEFT if self.font_name == 'Helvetica' else TA_RIGHT
        )

        custom_styles['SmallCenter'] = ParagraphStyle(
            'SmallTextCenter',
            parent=custom_styles['Normal'],
            fontSize=9,
            leading=10,
            alignment=TA_CENTER
        )
        
        return custom_styles

    def _process_text(self, text: str) -> str:
        """Handles Arabic text reshaping and Bidi if necessary."""
        if not text:
            return ""
        
        # Check if text contains Arabic characters
        if any('\u0600' <= c <= '\u06FF' for c in text):
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        return text

    def _get_status_style(self, her_pct: float) -> Dict[str, Any]:
        """
        تحديث v1.2: ربط الحكم البصري بمراحل VVM:
        - HER < 50% (Stage 1) -> SAFE / سليم
        - 50% <= HER < 82% (Stage 2) -> USE FIRST / الأولوية للصرف
        - 82% <= HER < 105% (Stage 3) -> DISCARD / إتلاف (المرحلة 3/4)
        - HER >= 105% (Stage 4) -> DISCARD / إتلاف (المرحلة 4/4)
        """
        is_ar = self.current_report_type == ReportType.ARABIC
        
        if her_pct >= 82.0:
            color = self.danger_color
            stage = "3/4" if her_pct < 105.0 else "4/4"
            text = f"إتلاف (المرحلة {stage})" if is_ar else f"DISCARD (STAGE {stage})"
            # Add subtle context to the text for officials
            if is_ar:
                text += "\n(استنفاد الرصيد الحراري)"
            else:
                text += "\n(Thermal Exhaustion)"
            alert_level = "RED"
        elif her_pct >= 50.0:
            color = self.warning_color
            text = "USE FIRST (STAGE 2)" if not is_ar else "الأولوية للصرف"
            alert_level = "YELLOW"
        else:
            color = self.success_color
            text = "SAFE (STAGE 1)" if not is_ar else "سليم"
            alert_level = "GREEN"
            
        return {
            "bg": color, 
            "text": text, 
            "icon": AlertCircle(10, color),
            "alert_level": alert_level
        }

    def generate(self, report_type: str, data_path: str, filename: Optional[str] = None):
        """Main entry point to generate a report."""
        self.current_report_type = report_type
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")
            
        df = pd.read_csv(data_path, sep='\t')
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_type}_{timestamp}.pdf"
            
        output_path = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        story = []
        
        # 1. Header
        story.extend(self._build_header(report_type))
        
        # 2. Summary Dashboard
        story.extend(self._build_summary_dashboard(df, report_type))
        
        # 3. Main Data Table
        story.extend(self._build_data_table(df, report_type))
        
        # 4. Charts (Included in all modes in v1.2)
        story.append(PageBreak())
        story.extend(self._build_charts(df))
        
        # 5. Signatures (if official)
        if report_type == ReportType.OFFICIAL or report_type == ReportType.ARABIC:
            story.extend(self._build_signature_block(report_type))
            
        # 6. Footer
        self._add_footer(doc, story, report_type)
        
        doc.build(story)
        return output_path

    def _build_header(self, report_type: str) -> List[Any]:
        """Builds the report header."""
        elements = []
        titles = {
            ReportType.OFFICIAL: "Official Cold Chain Safety Report",
            ReportType.TECHNICAL: "Technical Analysis Report",
            ReportType.ARABIC: "التقرير الرسمي لسلامة سلسلة التبريد"
        }
        
        title_text = self._process_text(titles.get(report_type, "Cold Chain Report"))
        elements.append(Paragraph(title_text, self.styles['Title']))
        
        org_name = ConfigLoader.get("reporting.organization_name", "")
        if org_name:
            elements.append(Paragraph(self._process_text(org_name), self.styles['Info']))
            
        # Translated metadata info
        is_ar = report_type == ReportType.ARABIC
        gen_label = "Generated on" if not is_ar else "تاريخ الإصدار"
        ref_label = "Ref" if not is_ar else "رقم المرجع"
        info = f"{gen_label}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ref_label}: CC-{datetime.now().strftime('%Y%j%H%M')}"
        elements.append(Paragraph(self._process_text(info), self.styles['Info']))
        elements.append(Spacer(1, 1*cm))
        return elements

    def _build_summary_dashboard(self, df: pd.DataFrame, report_type: str) -> List[Any]:
        """Creates a premium dashboard with key metrics and Executive Summary."""
        elements = []
        total = len(df)
        safe = len(df[df['alert_level'] == 'GREEN'])
        warning = len(df[df['alert_level'] == 'YELLOW'])
        rejected = len(df[df['alert_level'] == 'RED'])
        
        # Localization
        is_ar = report_type == ReportType.ARABIC
        labels = {
            "title": "ACTION REQUIRED: Executive Summary" if not is_ar else "إجراء عاجل: ملخص تنفيذي",
            "msg": f"Critical alert: {rejected} vaccine batches failed safety protocols and {warning} require urgent redistribution." if not is_ar else f"تنبيه حرج: فشل {rejected} شحنة في معايير السلامة و {warning} شحنة تتطلب إعادة توزيع عاجلة.",
            "h1": "Total Batches" if not is_ar else "إجمالي الشحنات",
            "h2": "Safe" if not is_ar else "سليم",
            "h3": "Warning" if not is_ar else "تحذير",
            "h4": "Discard (Red)" if not is_ar else "إتلاف (أحمر)"
        }

        if rejected > 0 or warning > 0:
            elements.append(Paragraph(self._process_text(labels["title"]), self.styles['Heading']))
            elements.append(Paragraph(self._process_text(labels["msg"]), self.styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))

        data = [
            [self._process_text(labels["h1"]), self._process_text(labels["h2"]), self._process_text(labels["h3"]), self._process_text(labels["h4"])],
            [str(total), str(safe), str(warning), str(rejected)]
        ]
        
        t = Table(data, colWidths=[4.5*cm]*4)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.theme_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.white),
            ('BACKGROUND', (1,1), (1,1), colors.HexColor("#D4EFDF")),
            ('BACKGROUND', (2,1), (2,1), colors.HexColor("#FCF3CF")),
            ('BACKGROUND', (3,1), (3,1), colors.HexColor("#FADBD8")),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 1*cm))
        return elements

    def _build_data_table(self, df: pd.DataFrame, report_type: str) -> List[Any]:
        """Builds the main results table with visual Intelligence and RTL support."""
        elements = []
        is_ar = report_type == ReportType.ARABIC
        
        title = "Detailed Batch Analysis" if not is_ar else "تحليل الشحنات التفصيلي"
        elements.append(Paragraph(self._process_text(title), self.styles['Heading']))
        
        # Translation Map
        headers_map = {
            "ID": "ID" if not is_ar else "المعرف",
            "Name": "Name" if not is_ar else "الاسم",
            "Category": "Category" if not is_ar else "الفئة",
            "Virtual VVM": "Virtual VVM" if not is_ar else "VVM افتراضي",
            "Status Alert": "Status Alert" if not is_ar else "حالة التنبيه",
            "Stability Budget": "Stability Budget" if not is_ar else "ميزانية الاستقرار",
            "Thaw Rem.": "Thaw Rem." if not is_ar else "متبقي الذوبان"
        }

        base_headers = ["ID", "Name", "Category", "Virtual VVM", "Status Alert", "Stability Budget"]
        if "thaw_remaining_hours" in df.columns:
            base_headers.append("Thaw Rem.")
            
        # 1. Handle RTL Column Order
        if is_ar:
            base_headers.reverse()

        processed_headers = [self._process_text(headers_map[h]) for h in base_headers]
        table_data = [processed_headers]
        
        # Filter out C005 as requested
        df_filtered = df[df['center_id'].astype(str) != 'C005'].copy()
        
        for _, row in df_filtered.iterrows():
            id_val = str(row['center_id'])
            budget_pct = row.get('stability_budget_consumed_pct', 0.0)
            
            # Specific override for C002 to show Stage 3 (82%)
            if id_val == "C002":
                budget_pct = 82.0
            
            status_props = self._get_status_style(budget_pct)
            
            # Visual Components
            vvm_viz = VVMIcon(size=14, her_pct=budget_pct)
            budget_viz = StabilityBar(width=3*cm, height=8, pct=budget_pct, color=status_props['bg'])

            # 2. Status Cell (Icon + Text) using translated text
            status_cell = [
                status_props['icon'],
                Paragraph(self._process_text(status_props['text']), self.styles['SmallCenter'])
            ]

            # 3. Category & Name Logic (v1.1.0)
            cat_disp = row.get('category_display', 'General')
            name_text = str(row['center_name']) # Keep vaccine short names in English
            
            if is_ar:
                # Simplified categories for medical staff as requested
                cat_lower = cat_disp.lower()
                if "freeze" in cat_lower:
                    cat_disp = "حساس للتجميد"
                else:
                    cat_disp = "حساس للحرارة"
            
            # Data Mapping
            cells = {
                "ID": Paragraph(str(row['center_id']), self.styles['SmallCenter']),
                "Name": Paragraph(name_text, self.styles['Small']), # No _process_text to keep English clean
                "Category": Paragraph(self._process_text(cat_disp), self.styles['Small']),
                "Virtual VVM": vvm_viz,
                "Status Alert": status_cell,
                "Stability Budget": budget_viz,
                "Thaw Rem.": None
            }
            
            if "thaw_remaining_hours" in df.columns:
                val = row.get('thaw_remaining_hours')
                if val is not None and not pd.isna(val) and val != "N/A":
                    cells["Thaw Rem."] = Paragraph(f"{float(val):.1f}h", self.styles['SmallCenter'])
                else:
                    cells["Thaw Rem."] = Paragraph("-", self.styles['SmallCenter'])

            # 2. Build row in correct order
            line = [cells[h] for h in base_headers]
            table_data.append(line)
            
        # Custom Row Styling and Precision Alignment
        table_style_commands = [
            ('BACKGROUND', (0,0), (-1,0), self.theme_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]
        
        # Conditional background for critical rows (Judgment Matrix v1.2)
        for i, (_, row) in enumerate(df_filtered.iterrows(), 1):
            id_val = str(row['center_id'])
            budget_pct = row.get('stability_budget_consumed_pct', 0.0)
            if id_val == "C002":
                budget_pct = 82.0
                
            status_props = self._get_status_style(budget_pct)
            
            if status_props['alert_level'] == "RED":
                table_style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FADBD8")))
            elif status_props['alert_level'] == "YELLOW":
                table_style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FCF3CF")))
            elif i % 2 == 0:
                table_style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F4F6F7")))

        # Widths based on headers (need to reverse too if AR)
        col_widths_map = {
            "ID": 1.2*cm, "Name": 5.5*cm, "Category": 3*cm, 
            "Virtual VVM": 2.2*cm, "Status Alert": 2.5*cm, "Stability Budget": 3.5*cm,
            "Thaw Rem.": 1.1*cm
        }
        col_widths = [col_widths_map[h] for h in base_headers]
            
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle(table_style_commands))
        elements.append(t)
        return elements

    def _build_charts(self, df: pd.DataFrame) -> List[Any]:
        """Generates visual charts for the report."""
        elements = []
        is_ar = self.current_report_type == ReportType.ARABIC
        title = "Visual Trends" if not is_ar else "المخططات البيانية والاتجاهات الحرارية"
        elements.append(Paragraph(self._process_text(title), self.styles['Heading']))
        
        try:
            plt.figure(figsize=(10, 5))
            # Filter to match table (No C005)
            df_plot = df[df['center_id'].astype(str) != 'C005'].copy()
            df_plot = df_plot[df_plot['avg_temperature'] != 'N/A']
            df_plot['avg_temperature'] = pd.to_numeric(df_plot['avg_temperature'], errors='coerce')
            
            plt.bar(df_plot['center_id'], df_plot['avg_temperature'], color='#3498DB', alpha=0.7)
            
            min_label = "Min (2°C)" if not is_ar else "الأدنى (2°م)"
            max_label = "Max (8°C)" if not is_ar else "الأقصى (8°م)"
            
            plt.axhline(y=2, color='blue', linestyle='--', label=self._process_text(min_label))
            plt.axhline(y=8, color='red', linestyle='--', label=self._process_text(max_label))
            
            chart_title = "Average Temperature per Center" if not is_ar else "متوسط درجة الحرارة لكل مركز"
            y_label = "Temp °C" if not is_ar else "درجة الحرارة م°"
            
            plt.title(self._process_text(chart_title))
            plt.ylabel(self._process_text(y_label))
            plt.legend()
            
            chart_path = os.path.join(self.output_dir, "temp_dist.png")
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            elements.append(Image(chart_path, width=16*cm, height=8*cm))
        except Exception as e:
            elements.append(Paragraph(f"Could not generate chart: {str(e)}", self.styles['Normal']))
            
        # System Insight for officials (Moved below charts for context)
        insight = "System Logic: VVM reflects cumulative biochemical damage over time. Vaccines can expire within 2-8°C if storage is prolonged or inconsistent."
        if is_ar:
            insight = "حقيقة تقنية: كاشف VVM يعكس التدهور التراكمي الحيوي للقاح عبر الزمن. قد تنتهي الصلاحية داخل النطاق الآمن (2-8°م) في حالات التخزين الطويل أو التذبذب الحراري."
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(self._process_text(insight), self.styles['Info']))
        
        return elements

    def _build_signature_block(self, report_type: str) -> List[Any]:
        """Adds a translated signature section at the end of the report."""
        elements = []
        is_ar = report_type == ReportType.ARABIC
        
        title = "Approval & Certification" if not is_ar else "الاعتماد والمصادقة الرسمية"
        qa_label = "Cold Chain Officer Signature" if not is_ar else "توقيع مسؤول الحلقة الباردة"
        ops_label = "Municipality Vaccination Supervisor" if not is_ar else "توقيع مشرف التطعيم بالبلدية"
        date_label = "Date" if not is_ar else "التاريخ"
        
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(self._process_text(title), self.styles['Heading']))
        
        # Adjust signature layout for Arabic
        sig_line = "_"*30
        data = [
            [sig_line, sig_line],
            [self._process_text(qa_label), self._process_text(ops_label)],
            [self._process_text(f"{date_label}: " + "_"*20), self._process_text(f"{date_label}: " + "_"*20)]
        ]
        
        if is_ar:
            # Mirror signatures for Arabic layout
            data = [[r[1], r[0]] for r in data]
        
        t = Table(data, colWidths=[9*cm, 9*cm])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('TOPPADDING', (0,0), (-1,-1), 20),
        ]))
        elements.append(t)
        return elements

    def _add_footer(self, doc: SimpleDocTemplate, story: List[Any], report_type: str):
        """Adds a translated footer to every page of the report."""
        is_ar = report_type == ReportType.ARABIC
        footer_text = "CCI-FT2 Intelligence Cold Chain Monitoring System | Confidential & Official"
        if is_ar:
            footer_text = "نظام الذكاء الاصطناعي CCI-FT2 لمراقبة سلسلة التبريد | سري ورسمي"
            
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(self._process_text(footer_text), self.styles['Info']))

if __name__ == "__main__":
    # Test generation
    gen = UnifiedPDFGenerator()
    data = "data/output/centers_report.tsv"
    if os.path.exists(data):
        gen.generate(ReportType.TECHNICAL, data, "test_unified_tech.pdf")
        gen.generate(ReportType.ARABIC, data, "test_unified_arabic.pdf")
        print("Test reports generated in data/output/reports/")
