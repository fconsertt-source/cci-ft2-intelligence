# =============================================
# 📄 سكربت إنشاء تقرير PDF رسمي (يدعم العربية) - إصلاح كامل
# اسم الملف: arabic_pdf_generator_fixed.py
# المسار: src/reporting/arabic_pdf_generator_fixed.py
# =============================================

import pandas as pd
from datetime import datetime
import os
import sys
import io

# محاولة إصلاح ترميز الكونسول على Windows
try:
    # لمستخدمي Windows: تغيير الترميز إلى UTF-8
    import sys
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')
except:
    pass

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
try:
    from reportlab.pdfbase import pdfmetrics
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def safe_print(message):
    """طباعة آمنة تتجنب مشاكل الترميز"""
    try:
        print(message)
    except:
        # إذا فشلت الطباعة، حاول بطريقة أخرى
        try:
            print(message.encode('utf-8', errors='ignore').decode('ascii', errors='ignore'))
        except:
            print("[Printed message with encoding issues]")

def setup_arabic_fonts():
    """إعداد الخطوط العربية لـ ReportLab"""
    
    try:
        # استخدام Arial المتوفر على Windows
        font_path = 'C:/Windows/Fonts/arial.ttf'
        
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
            safe_print("INFO: Using Arabic font from: " + font_path)
            return 'ArabicFont'
        else:
            # حاول مع خطوط أخرى
            alt_paths = [
                'C:/Windows/Fonts/tahoma.ttf',
                'C:/Windows/Fonts/segoeui.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/System/Library/Fonts/Helvetica.ttf'
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    pdfmetrics.registerFont(TTFont('ArabicFont', alt_path))
                    safe_print("INFO: Using alternative font from: " + alt_path)
                    return 'ArabicFont'
        
        safe_print("INFO: Using default Helvetica font")
        return 'Helvetica'
        
    except Exception as e:
        safe_print("WARNING: Error loading font: " + str(e))
        return 'Helvetica'

def create_arabic_pdf():
    """إنشاء تقرير PDF بالعربية بشكل صحيح"""
    
    safe_print("INFO: Starting Arabic PDF report generation...")
    
    # إعداد الخطوط
    arabic_font = setup_arabic_fonts()
    
    # المسارات
    input_file = "data/output/centers_report.tsv"
    output_dir = "data/output/reports"
    output_file = os.path.join(output_dir, "cold_chain_official_report.pdf")
    
    # التأكد من وجود المجلد
    os.makedirs(output_dir, exist_ok=True)
    
    # قراءة البيانات
    if not os.path.exists(input_file):
        safe_print("ERROR: Report file not found: " + input_file)
        return None
    
    try:
        df = pd.read_csv(input_file, sep='\t')
        safe_print(f"INFO: Read {len(df)} records from data")
    except Exception as e:
        safe_print(f"ERROR: Failed to read data file: {str(e)}")
        return None
    
    try:
        # إعداد وثيقة PDF
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="Cold Chain Monitoring Report"
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # ========== إنشاء أنماط مخصصة للعربية ==========
        arabic_title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Heading1'],
            fontName=arabic_font,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#2C3E50')
        )
        
        arabic_heading_style = ParagraphStyle(
            'ArabicHeading',
            parent=styles['Heading2'],
            fontName=arabic_font,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#3498DB')
        )
        
        arabic_normal_style = ParagraphStyle(
            'ArabicNormal',
            parent=styles['Normal'],
            fontName=arabic_font,
            fontSize=11,
            alignment=TA_RIGHT,
            spaceAfter=10
        )
        
        arabic_center_style = ParagraphStyle(
            'ArabicCenter',
            parent=styles['Normal'],
            fontName=arabic_font,
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        # ========== إضافة ترويسة التقرير ==========
        # نكتب النص العربي مباشرة (ReportLab سيتعامل معه)
        title_text = "التقرير الرسمي لمراقبة سلسلة التبريد"
        story.append(Paragraph(title_text, arabic_title_style))
        
        subtitle_text = "نظام CCI-FT2 - المراقبة الذكية لسلسلة التبريد"
        story.append(Paragraph(subtitle_text, arabic_heading_style))
        
        # معلومات التقرير
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_info = "تاريخ إنشاء التقرير: " + report_date
        story.append(Paragraph(report_info, arabic_center_style))
        
        ref_number = "CC-" + datetime.now().strftime('%Y%m%d-%H%M%S')
        ref_info = "رقم المرجع: " + ref_number
        story.append(Paragraph(ref_info, arabic_center_style))
        
        story.append(Spacer(1, 30))
        
        # ========== جدول البيانات الرئيسي ==========
        story.append(Paragraph("النتائج التفصيلية", arabic_heading_style))
        
        table_data = []
        
        # عناوين الجدول
        headers = [
            "رقم المركز",
            "اسم المركز",
            "القرار",
            "متوسط الحرارة",
            "الحالة"
        ]
        
        table_data.append(headers)
        
        # إضافة البيانات
        for index, row in df.iterrows():
            decision = str(row['decision'])
            center_name = str(row['center_name'])
            
            # تحديد حالة اللون والنص
            if 'REJECTED' in decision:
                status_text = "مرفوض"
            elif 'NO_DATA' in decision:
                status_text = "لا بيانات"
            elif 'ACCEPTED' in decision:
                status_text = "مقبول"
            elif 'WARNING' in decision:
                status_text = "تحذير"
            else:
                status_text = "غير معروف"
            
            table_row = [
                str(row['center_id']),
                center_name,
                decision,
                str(round(row['avg_temperature'], 2)) + " °C",
                status_text
            ]
            table_data.append(table_row)
        
        # إنشاء الجدول
        table = Table(table_data, colWidths=[3*cm, 5*cm, 3.5*cm, 3*cm, 2.5*cm])
        
        # تنسيق الجدول الأساسي
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), arabic_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])
        
        # تلوين الصفوف بناءً على الحالة
        for i in range(1, len(table_data)):
            status = table_data[i][4]
            if "مرفوض" in status:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
            elif "لا بيانات" in status:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
            elif "مقبول" in status:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
            elif "تحذير" in status:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightyellow)
        
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 30))
        
        # ========== ملخص النتائج ==========
        story.append(Paragraph("ملخص النتائج", arabic_heading_style))
        
        # إحصائيات
        total = len(df)
        rejected = len(df[df['decision'].str.contains('REJECTED', na=False)])
        accepted = len(df[df['decision'].str.contains('ACCEPTED', na=False)])
        warning = len(df[df['decision'].str.contains('WARNING', na=False)])
        no_data = len(df[df['decision'].str.contains('NO_DATA', na=False)])
        
        summary_data = [
            ["المؤشر", "العدد", "النسبة"],
            ["إجمالي المراكز", str(total), "100%"],
            ["المراكز المقبولة", str(accepted), f"{accepted/total*100:.1f}%" if total > 0 else "0%"],
            ["المراكز تحت المراقبة", str(warning), f"{warning/total*100:.1f}%" if total > 0 else "0%"],
            ["المراكز المرفوضة", str(rejected), f"{rejected/total*100:.1f}%" if total > 0 else "0%"],
            ["لا بيانات", str(no_data), f"{no_data/total*100:.1f}%" if total > 0 else "0%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 3*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 40))
        
        # ========== منطقة التوقيعات ==========
        story.append(Paragraph("التوقيعات والاعتمادات", arabic_heading_style))
        
        signatures = [
            ("________________________", "مدير مراقبة الجودة"),
            ("________________________", "مدير سلسلة التبريد"),
            ("________________________", "المدير الطبي"),
        ]
        
        for line, title in signatures:
            story.append(Spacer(1, 15))
            story.append(Paragraph(line, arabic_center_style))
            story.append(Paragraph(title, arabic_center_style))
        
        story.append(Spacer(1, 40))
        
        # ========== تذييل الصفحة ==========
        footer_text = """
        هذا التقرير صادر عن نظام CCI-FT2 للمراقبة الذكية لسلسلة التبريد.
        جميع البيانات الواردة في هذا التقرير معتمدة من النظام الآلي.
        للحصول على نسخ إلكترونية أو استفسارات: cc-monitoring@organization.org
        """
        
        story.append(Paragraph(footer_text, arabic_center_style))
        
        # تاريخ الإصدار
        release_date = "تاريخ الإصدار: " + datetime.now().strftime("%Y-%m-%d")
        story.append(Paragraph(release_date, arabic_center_style))
        
        # ========== إنشاء PDF ==========
        safe_print("INFO: Creating PDF file...")
        doc.build(story)
        
        safe_print(f"SUCCESS: Report created successfully: {output_file}")
        safe_print(f"INFO: Report statistics:")
        safe_print(f"  - Total centers: {total}")
        safe_print(f"  - Accepted: {accepted}")
        safe_print(f"  - Warning: {warning}")
        safe_print(f"  - Rejected: {rejected}")
        safe_print(f"  - No data: {no_data}")
        
        return output_file
        
    except Exception as e:
        safe_print(f"ERROR: Failed to create PDF: {str(e)}")
        import traceback
        safe_print("DEBUG: Error details:")
        safe_print(traceback.format_exc())
        return None

def create_simple_pdf():
    """دالة توافقية مع السكربت القديم"""
    return create_arabic_pdf()

if __name__ == "__main__":
    # إنشاء التقرير
    result = create_arabic_pdf()
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)