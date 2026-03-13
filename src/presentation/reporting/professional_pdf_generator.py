# =============================================
# 📄 سكربت إنشاء تقرير PDF رسمي (قابل للتوقيع)
# =============================================
# اسم الملف: professional_pdf_generator.py
# المسار: src/reporting/professional_pdf_generator.py
# =============================================

import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

def create_professional_pdf():
    """إنشاء تقرير PDF احترافي قابل للتوقيع والاعتماد"""
    
    # المسارات
    input_file = "data/output/centers_report.tsv"
    output_dir = "data/output/reports"
    output_file = os.path.join(output_dir, "cold_chain_official_report.pdf")
    
    # التأكد من وجود المجلد
    os.makedirs(output_dir, exist_ok=True)
    
    # قراءة البيانات
    if not os.path.exists(input_file):
        print("❌ ملف التقرير غير موجود:", input_file)
        return
    
    df = pd.read_csv(input_file, sep='\t')
    
    # إعداد وثيقة PDF
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ========== إضافة ترويسة التقرير ==========
    # العنوان الرئيسي
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#2C3E50')
    )
    
    title = Paragraph("التقرير الرسمي لمراقبة سلسلة التبريد", title_style)
    story.append(title)
    
    # العنوان الفرعي
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#3498DB')
    )
    
    subtitle = Paragraph("نظام CCI-FT2 - المراقبة الذكية لسلسلة التبريد", subtitle_style)
    story.append(subtitle)
    
    # معلومات التقرير
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.grey
    )
    
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_info = f"تاريخ إنشاء التقرير: {report_date} | رقم المرجع: CC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    story.append(Paragraph(report_info, info_style))
    
    story.append(Spacer(1, 20))
    
    # ========== جدول البيانات الرئيسي ==========
    # إعداد بيانات الجدول
    table_data = []
    
    # عناوين الأعمدة (مع ترجمة)
    arabic_headers = [
        "رقم المركز",
        "اسم المركز", 
        "القرار",
        "مرحلة VVM",
        "الإجراء الموصى به",
        "عدد القراءات",
        "تجميد؟",
        "مخالفة؟",
        "متوسط °C",
        "أدنى °C",
        "أعلى °C"
    ]
    
    table_data.append(arabic_headers)
    
    # إضافة البيانات
    for _, row in df.iterrows():
        table_row = [
            row['center_id'],
            row['center_name'],
            translate_decision(row['decision']),
            row['vvm_stage'],
            row['recommended_action'],
            str(row['num_ft2_entries']),
            "نعم" if row['has_freeze'] == 'YES' else "لا",
            "نعم" if row['has_ccm_violation'] == 'YES' else "لا",
            f"{row['avg_temperature']:.2f}",
            f"{row['min_temperature']:.2f}",
            f"{row['max_temperature']:.2f}"
        ]
        table_data.append(table_row)
    
    # إنشاء الجدول
    table = Table(table_data, colWidths=[3*cm, 4*cm, 3*cm, 2*cm, 5*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    
    # تنسيق الجدول
    table.setStyle(TableStyle([
        # تنسيق الرأس
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # خطوط الشبكة
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        
        # تنسيق الصفوف بناءً على القرار
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightcoral),  # مرفوض
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightcoral),  # مرفوض
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),   # لا بيانات
        
        # جعل بعض الأعمدة أوسع للنص العربي
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # اسم المركز
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # الإجراء الموصى به
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # ========== ملخص النتائج ==========
    summary_style = ParagraphStyle(
        'CustomSummary',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#2C3E50')
    )
    
    story.append(Paragraph("ملخص النتائج", summary_style))
    
    # إحصائيات
    total = len(df)
    rejected = len(df[df['decision'].str.contains('REJECTED')])
    accepted = len(df[df['decision'].str.contains('ACCEPTED')])
    warning = len(df[df['decision'].str.contains('WARNING')])
    no_data = len(df[df['decision'].str.contains('NO_DATA')])
    
    summary_data = [
        ["المؤشر", "العدد", "النسبة"],
        ["إجمالي المراكز", str(total), "100%"],
        ["مقبولة", str(accepted), f"{(accepted/total*100):.1f}%" if total > 0 else "0%"],
        ["تحت المراقبة", str(warning), f"{(warning/total*100):.1f}%" if total > 0 else "0%"],
        ["مرفوضة", str(rejected), f"{(rejected/total*100):.1f}%" if total > 0 else "0%"],
        ["لا بيانات", str(no_data), f"{(no_data/total*100):.1f}%" if total > 0 else "0%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 3*cm, 3*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightyellow),
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightcoral),
        ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 40))
    
    # ========== منطقة التوقيعات ==========
    sign_style = ParagraphStyle(
        'CustomSign',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceBefore=20
    )
    
    # خطوط التوقيع
    story.append(Paragraph("_" * 50, sign_style))
    story.append(Paragraph("مدير مراقبة الجودة", sign_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("_" * 50, sign_style))
    story.append(Paragraph("مدير سلسلة التبريد", sign_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("_" * 50, sign_style))
    story.append(Paragraph("المدير الطبي", sign_style))
    
    # ========== تذييل الصفحة ==========
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceBefore=50
    )
    
    footer_text = """
    هذا التقرير صادر عن نظام CCI-FT2 للمراقبة الذكية لسلسلة التبريد.
    جميع البيانات الواردة في هذا التقرير معتمدة من النظام الآلي.
    للحصول على نسخ إلكترونية أو استفسارات: cc-monitoring@organization.org
    """
    
    story.append(Spacer(1, 50))
    story.append(Paragraph(footer_text, footer_style))
    
    # ========== إنشاء PDF ==========
    doc.build(story)
    print(f"✅ تم إنشاء التقرير الرسمي: {output_file}")
    
    return output_file

def translate_decision(decision):
    """ترجمة القرار للإنجليزية/العربية"""
    translations = {
        'REJECTED_FREEZE_SENSITIVE': 'مرفوض (تجميد)',
        'NO_DATA': 'لا بيانات',
        'ACCEPTED': 'مقبول',
        'WARNING': 'تحت المراقبة',
        'REJECTED': 'مرفوض'
    }
    
    for key, value in translations.items():
        if key in str(decision):
            return value
    
    return decision

# =============================================
# دالة مساعدة للاستخدام من السكربت الرئيسي
# =============================================
def create_simple_pdf():
    """دالة توافقية مع السكربت القديم"""
    return create_professional_pdf()

if __name__ == "__main__":
    create_professional_pdf()