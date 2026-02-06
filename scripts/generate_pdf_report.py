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
from src.presentation.messages.message_map import MessageProvider

logger = get_logger(__name__)

def main():
    logger.info(MessageProvider.get('PDF_GENERATION_START'))
    logger.info("%s", "="*50)
    
    # المسار إلى بيانات TSV
    tsv_path = "data/output/centers_report.tsv"
    
    if not os.path.exists(tsv_path):
        logger.error(MessageProvider.get('PDF_SOURCE_FILE_MISSING', path=tsv_path))
        logger.info(MessageProvider.get('PDF_RUN_PIPELINE_HINT'))
        logger.info(MessageProvider.get('PDF_RUN_PIPELINE_CMD'))
        return
    
    logger.info(MessageProvider.get('PDF_READING_DATA', path=tsv_path))
    
    # إنشاء مولد التقارير (تحميل لاحق لتجنب استيراد ثقيل أثناء الاختبارات)
    try:
        from src.presentation.reporting.pdf_generator import PDFReportGenerator
    except Exception as e:
        logger.error("لا يمكن استيراد مولد PDF: %s", e)
        return

    generator = PDFReportGenerator()

    # إنشاء التقرير
    logger.info(MessageProvider.get('PDF_GENERATION_IN_PROGRESS'))
    report_path = generator.generate_report(tsv_path)
    
    if report_path:
        logger.info("\n" + MessageProvider.get('PDF_GENERATION_SUCCESS'))
        logger.info(MessageProvider.get('PDF_LOCATION', path=report_path))
        try:
            size_kb = os.path.getsize(report_path) / 1024.0
            logger.info(MessageProvider.get('PDF_SIZE', size=size_kb))
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
                logger.info(MessageProvider.get('PDF_AUTO_OPENED'))
            except Exception:
                logger.info(MessageProvider.get('PDF_MANUAL_OPEN_HINT'))
    else:
        logger.error(MessageProvider.get('PDF_GENERATION_FAILED'))

if __name__ == "__main__":
    main()