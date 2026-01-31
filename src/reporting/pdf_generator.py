<<<<<<< HEAD
"""Lightweight PDF generator shim used when no concrete PDF generator
implementation is available. Tests will typically patch `PDFReportGenerator`.
"""

from __future__ import annotations

class PDFReportGenerator:
    """Shim class for tests and lightweight execution.

    Production deployments can provide a richer implementation in
    `src.reporting.pdf_generator` that implements the same `generate_report`
    method signature.
    """

    def __init__(self, *args, **kwargs) -> None:
        pass

    def generate_report(self, tsv_path: str) -> str:
        """Generate a PDF from the TSV at `tsv_path`.

        This shim raises NotImplementedError to indicate that a real
        implementation should be provided by the deployment or patched in
        tests.
        """
        raise NotImplementedError("PDFReportGenerator.generate_report is not implemented in this environment")
=======
"""
مولد تقارير PDF احترافي
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # للاستخدام بدون واجهة رسومية

class PDFReportGenerator:
    """مولد تقارير PDF احترافي"""
    
    def __init__(self, output_dir="data/output/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # تسجيل الخطوط العربية
        try:
            # استخدام خط افتراضي أو خط موجود
            self.font_path = self._find_arabic_font()
            if self.font_path:
                pdfmetrics.registerFont(TTFont('Arabic', self.font_path))
        except:
            print("⚠️  تحذير: لم يتم العثور على خط عربي، سيتم استخدام الخط الافتراضي")
    
    def _find_arabic_font(self):
        """البحث عن خط عربي في النظام"""
        font_paths = [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/tahoma.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf'
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _arabic_text(self, text):
        """معالجة النصوص العربية"""
        if not text:
            return ""
        
        # إعادة تشكيل النص العربي
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    def _create_header(self, story, title):
        """إنشاء رأس التقرير"""
        # عنوان التقرير
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Title'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1,  # مركز
            spaceAfter=20
        )
        
        story.append(Paragraph(self._arabic_text(title), title_style))
        
        # معلومات التاريخ والوقت
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_style = ParagraphStyle(
            'CustomDate',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=1,
            spaceAfter=30
        )
        
        story.append(Paragraph(self._arabic_text(f"تاريخ التقرير: {date_str}"), date_style))
        
        # خط فاصل
        story.append(Spacer(1, 10))
    
    def _create_summary_table(self, story, data):
        """إنشاء جدول الملخص"""
        # رأس الجدول
        headers = [
            'المركز', 'المعرف', 'القرار', 'مرحلة VVM', 
            'متوسط الحرارة', 'الحالة', 'التوصية'
        ]
        
        # تحويل البيانات
        table_data = [headers]
        
        for idx, row in data.iterrows():
            # تحديد لون الحالة
            status_color = self._get_status_color(row['decision'])
            
            # تحويل البيانات العربية
            row_data = [
                self._arabic_text(row['center_name']),
                row['center_id'],
                self._arabic_text(row['decision']),
                row['vvm_stage'],
                f"{row['avg_temperature']}°C" if row['avg_temperature'] != 'N/A' else 'N/A',
                self._arabic_text(status_color['text']),
                self._arabic_text(row['recommended_action'][:50] + '...' if len(str(row['recommended_action'])) > 50 else row['recommended_action'])
            ]
            table_data.append(row_data)
        
        # إنشاء الجدول
        table = Table(table_data, colWidths=[3*cm, 2*cm, 3*cm, 2*cm, 2.5*cm, 2.5*cm, 5*cm])
        
        # تنسيق الجدول
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('FONTNAME', (0, 1), (-1, -1), 'Arabic' if self.font_path else 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # إضافة تلوين للخلايا بناءً على القرار
        for i in range(1, len(table_data)):
            status_color = self._get_status_color(data.iloc[i-1]['decision'])
            if status_color['color']:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (2, i), (2, i), status_color['color']),
                    ('TEXTCOLOR', (2, i), (2, i), colors.white),
                ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
    
    def _get_status_color(self, decision):
        """الحصول على لون الحالة بناءً على القرار"""
        if 'ACCEPTED' in decision:
            return {'color': colors.HexColor('#27ae60'), 'text': '✅ سليم'}
        elif 'WARNING' in decision:
            return {'color': colors.HexColor('#f39c12'), 'text': '⚠️ تحذير'}
        elif 'REJECTED' in decision:
            return {'color': colors.HexColor('#e74c3c'), 'text': '❌ مرفوض'}
        else:
            return {'color': colors.gray, 'text': '❓ غير معروف'}
    
    def _create_statistics_section(self, story, data):
        """إنشاء قسم الإحصائيات"""
        # عنوان القسم
        title_style = ParagraphStyle(
            'SectionTitle',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10
        )
        
        story.append(Paragraph(self._arabic_text("📊 الإحصائيات العامة"), title_style))
        
        # حساب الإحصائيات
        total = len(data)
        accepted = len(data[data['decision'].str.contains('ACCEPTED')])
        warnings = len(data[data['decision'].str.contains('WARNING')])
        rejected = len(data[data['decision'].str.contains('REJECTED')])
        
        # إنشاء جدول الإحصائيات
        stats_data = [
            ['المؤشر', 'القيمة', 'النسبة'],
            ['إجمالي المراكز', str(total), '100%'],
            ['المراكز السليمة', str(accepted), f'{accepted/total*100:.1f}%'],
            ['المراكز تحت تحذير', str(warnings), f'{warnings/total*100:.1f}%'],
            ['المراكز المرفوضة', str(rejected), f'{rejected/total*100:.1f}%']
        ]
        
        # تحويل النصوص العربية
        for i in range(len(stats_data)):
            stats_data[i][0] = self._arabic_text(stats_data[i][0])
        
        stats_table = Table(stats_data, colWidths=[4*cm, 3*cm, 3*cm])
        
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('FONTNAME', (0, 1), (-1, -1), 'Arabic' if self.font_path else 'Helvetica'),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
    
    def _create_temperature_chart(self, story, data):
        """إنشاء مخطط درجات الحرارة"""
        try:
            # تحضير البيانات للمخطط
            centers = []
            avg_temps = []
            colors_list = []
            
            for _, row in data.iterrows():
                if row['avg_temperature'] != 'N/A':
                    centers.append(self._arabic_text(row['center_name']))
                    avg_temps.append(float(row['avg_temperature']))
                    
                    # تحديد اللون بناءً على القرار
                    if 'ACCEPTED' in row['decision']:
                        colors_list.append('#27ae60')  # أخضر
                    elif 'WARNING' in row['decision']:
                        colors_list.append('#f39c12')  # أصفر
                    elif 'REJECTED' in row['decision']:
                        colors_list.append('#e74c3c')  # أحمر
                    else:
                        colors_list.append('#95a5a6')  # رمادي
            
            if avg_temps:
                # إنشاء المخطط
                plt.figure(figsize=(8, 4))
                bars = plt.bar(centers, avg_temps, color=colors_list, edgecolor='black')
                
                # إضافة القيم على الأعمدة
                for bar, temp in zip(bars, avg_temps):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{temp:.1f}°C', ha='center', va='bottom')
                
                # إضافة خطوط الإرشاد
                plt.axhline(y=2, color='blue', linestyle='--', alpha=0.5, label='الحد الأدنى (2°C)')
                plt.axhline(y=8, color='red', linestyle='--', alpha=0.5, label='الحد الأقصى (8°C)')
                
                plt.title('متوسط درجات الحرارة للمراكز', fontname='Arial', fontsize=14)
                plt.xlabel('المراكز', fontname='Arial')
                plt.ylabel('درجة الحرارة (°C)', fontname='Arial')
                plt.ylim(-5, max(avg_temps) + 5)
                plt.xticks(rotation=45, ha='right')
                plt.legend()
                plt.tight_layout()
                
                # حفظ المخطط كصورة
                chart_path = os.path.join(self.output_dir, 'temperature_chart.png')
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # إضافة الصورة للتقرير
                story.append(Spacer(1, 20))
                title_style = ParagraphStyle(
                    'ChartTitle',
                    parent=getSampleStyleSheet()['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#2c3e50'),
                    spaceAfter=10
                )
                
                story.append(Paragraph(self._arabic_text("📈 مخطط درجات الحرارة"), title_style))
                story.append(Image(chart_path, width=15*cm, height=8*cm))
                story.append(Spacer(1, 20))
                
        except Exception as e:
            print(f"⚠️  لم يتم إنشاء المخطط: {e}")
    
    def _create_recommendations_section(self, story, data):
        """إنشاء قسم التوصيات"""
        title_style = ParagraphStyle(
            'SectionTitle',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10
        )
        
        story.append(Paragraph(self._arabic_text("💡 التوصيات والإجراءات"), title_style))
        
        recommendations = []
        
        # تحليل البيانات لتوليد توصيات
        for _, row in data.iterrows():
            if 'REJECTED' in row['decision']:
                recommendations.append(f"🚨 **{row['center_name']}**: {row['recommended_action']}")
            elif 'WARNING' in row['decision']:
                recommendations.append(f"⚠️  **{row['center_name']}**: {row['recommended_action']}")
        
        if not recommendations:
            recommendations.append("✅ **جميع المراكز سليمة**: لا توجد إجراءات عاجلة مطلوبة")
        
        # إضافة توصيات عامة
        recommendations.append("📋 **مراقبة دورية**: فحص أجهزة القياس أسبوعياً")
        recommendations.append("🧹 **صيانة دورية**: تنظيف وفحص ثلاجات التخزين")
        recommendations.append("📊 **تدقيق البيانات**: مراجعة التقارير الشهرية")
        
        # إضافة التوصيات كمصفوفة
        rec_data = [[self._arabic_text(rec)] for rec in recommendations]
        
        rec_table = Table(rec_data, colWidths=[18*cm])
        
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic' if self.font_path else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(rec_table)
        story.append(Spacer(1, 20))
    
    def _create_footer(self, story):
        """إنشاء تذييل التقرير"""
        footer_style = ParagraphStyle(
            'Footer',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=1,
            spaceBefore=30
        )
        
        footer_text = """
        تم إنشاء هذا التقرير تلقائياً بواسطة نظام مراقبة سلسلة التبريد (CCI-FT2 Intelligence)<br/>
        نظام مطابق لمتطلبات WHO و CDC لمراقبة لقاحات COVID-19 واللقاحات الأخرى<br/>
        تاريخ الإنشاء: {date} | الإصدار: 2.0.0
        """.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        story.append(Paragraph(self._arabic_text(footer_text), footer_style))
    
    def generate_report(self, tsv_path, output_filename=None):
        """إنشاء تقرير PDF كامل"""
        
        # قراءة بيانات TSV
        try:
            df = pd.read_csv(tsv_path, delimiter='\t', encoding='utf-8')
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف TSV: {e}")
            return None
        
        # تحديد اسم ملف الإخراج
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"cold_chain_report_{timestamp}.pdf"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # إنشاء مستند PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # قصة التقرير (عناصر التقرير)
        story = []
        
        # 1. رأس التقرير
        self._create_header(story, "تقرير مراقبة سلسلة التبريد - لقاحات COVID-19")
        
        # 2. جدول الملخص
        self._create_summary_table(story, df)
        
        # 3. قسم الإحصائيات
        self._create_statistics_section(story, df)
        
        # 4. مخطط درجات الحرارة
        self._create_temperature_chart(story, df)
        
        # 5. قسم التوصيات
        self._create_recommendations_section(story, df)
        
        # 6. التذييل
        self._create_footer(story)
        
        # بناء التقرير
        try:
            doc.build(story)
            print(f"✅ تم إنشاء التقرير: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ خطأ في إنشاء PDF: {e}")
            return None

# دالة مساعدة للاستخدام السريع
def generate_pdf_report():
    """دالة مساعدة لإنشاء تقرير PDF"""
    generator = PDFReportGenerator()
    tsv_path = "data/output/centers_report.tsv"
    
    if os.path.exists(tsv_path):
        return generator.generate_report(tsv_path)
    else:
        print(f"❌ ملف TSV غير موجود: {tsv_path}")
        return None

if __name__ == "__main__":
    report_path = generate_pdf_report()
    if report_path:
        print(f"📄 التقرير جاهز: {report_path}")
>>>>>>> a401e3c103f41075e342c0dfd67bb255c2193010
