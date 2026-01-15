#!/usr/bin/env python
"""
سكربت لإنشاء تقرير PDF بضغطة واحدة
"""
import sys
import os
from pathlib import Path

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from src.reporting.pdf_generator import PDFReportGenerator

def main():
    print("📄 إنشاء تقرير PDF احترافي")
    print("="*50)
    
    # المسار إلى بيانات TSV
    tsv_path = "data/output/centers_report.tsv"
    
    if not os.path.exists(tsv_path):
        print(f"❌ ملف التقرير غير موجود: {tsv_path}")
        print("⚠️  قم بتشغيل النظام أولاً:")
        print("   python -m scripts.run_ft2_pipeline --legacy")
        return
    
    print(f"📊 قراءة البيانات من: {tsv_path}")
    
    # إنشاء مولد التقارير
    generator = PDFReportGenerator()
    
    # إنشاء التقرير
    print("🔄 جاري إنشاء التقرير...")
    report_path = generator.generate_report(tsv_path)
    
    if report_path:
        print(f"\n✅ تم إنشاء التقرير بنجاح!")
        print(f"📍 الموقع: {report_path}")
        print(f"📏 الحجم: {os.path.getsize(report_path) / 1024:.1f} KB")
        
        # فتح التقرير تلقائياً
        try:
            if sys.platform == "win32":
                os.startfile(report_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{report_path}'")
            else:  # Linux
                os.system(f"xdg-open '{report_path}'")
            print("📂 تم فتح التقرير تلقائياً")
        except:
            print("💡 يمكنك فتح التقرير يدوياً من المسار أعلاه")
    else:
        print("❌ فشل في إنشاء التقرير")

if __name__ == "__main__":
    main()