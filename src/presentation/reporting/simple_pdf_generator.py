import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import pandas as pd

class SimplePDFGenerator:
    def generate_report(self, tsv_path, output_path):
        try:
            # قراءة البيانات
            df = pd.read_csv(tsv_path, delimiter='\t', encoding='utf-8')
            
            # إنشاء PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # العنوان
            title = Paragraph("تقرير مراقبة سلسلة التبريد", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # التاريخ
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_text = Paragraph(f"تاريخ التقرير: {date_str}", styles['Normal'])
            story.append(date_text)
            story.append(Spacer(1, 30))
            
            # تحضير بيانات الجدول
            table_data = [['المركز', 'القرار', 'VVM', 'الحرارة', 'التوصية']]
            
            for _, row in df.iterrows():
                table_data.append([
                    row['center_name'],
                    row['decision'],
                    row['vvm_stage'],
                    row['avg_temperature'],
                    row['recommended_action'][:50] + '...' if len(str(row['recommended_action'])) > 50 else row['recommended_action']
                ])
            
            # إنشاء الجدول
            table = Table(table_data, colWidths=[4*cm, 3*cm, 2*cm, 3*cm, 6*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
                ('GRID', (0,0), (-1,-1), 1, colors.gray),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 40))
            
            # التذييل
            footer = Paragraph("تم إنشاء هذا التقرير تلقائياً بواسطة نظام CCI-FT2 Intelligence", styles['Normal'])
            story.append(footer)
            
            # بناء التقرير
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"خطأ في إنشاء PDF: {e}")
            return False

def create_simple_pdf():
    generator = SimplePDFGenerator()
    tsv_path = "data/output/centers_report.tsv"
    output_path = "data/output/reports/cold_chain_report.pdf"
    
    if os.path.exists(tsv_path):
        success = generator.generate_report(tsv_path, output_path)
        if success:
            print(f"✅ تم إنشاء التقرير: {output_path}")
            return output_path
    else:
        print(f"❌ ملف TSV غير موجود: {tsv_path}")
    
    return None
