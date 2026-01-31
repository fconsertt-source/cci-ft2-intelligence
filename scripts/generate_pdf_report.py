#!/usr/bin/env python
"""
سكربت لإنشاء تقرير PDF بضغطة واحدة
"""
import sys
import os
from pathlib import Path

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

def main():
    logger.info("📄 إنشاء تقرير PDF احترافي")
    logger.info("%s", "="*50)
    
    # المسار إلى بيانات TSV
    tsv_path = "data/output/centers_report.tsv"
    
    if not os.path.exists(tsv_path):
        logger.error("❌ ملف التقرير غير موجود: %s", tsv_path)
        logger.info("⚠️  قم بتشغيل النظام أولاً:")
        logger.info("   python -m scripts.run_ft2_pipeline --legacy")
        return
    
    logger.info("📊 قراءة البيانات من: %s", tsv_path)
    
    # إنشاء مولد التقارير (تحميل لاحق لتجنب استيراد ثقيل أثناء الاختبارات)
    try:
        from src.reporting.pdf_generator import PDFReportGenerator
    except Exception as e:
        logger.error("لا يمكن استيراد مولد PDF: %s", e)
        return

    generator = PDFReportGenerator()

    # إنشاء التقرير
    logger.info("🔄 جاري إنشاء التقرير...")
    report_path = generator.generate_report(tsv_path)
    
    if report_path:
        logger.info("\n✅ تم إنشاء التقرير بنجاح!")
        logger.info("📍 الموقع: %s", report_path)
        try:
            size_kb = os.path.getsize(report_path) / 1024.0
            logger.info("📏 الحجم: %.1f KB", size_kb)
        except Exception:
            logger.debug("تعذر الحصول على حجم الملف: %s", report_path)
        
        # فتح التقرير تلقائياً
            try:
                if sys.platform == "win32":
                    os.startfile(report_path)
                elif sys.platform == "darwin":  # macOS
                    os.system(f"open '{report_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{report_path}'")
                logger.info("📂 تم فتح التقرير تلقائياً")
            except Exception:
                logger.info("💡 يمكنك فتح التقرير يدوياً من المسار أعلاه")
    else:
        logger.error("❌ فشل في إنشاء التقرير")

if __name__ == "__main__":
    main()