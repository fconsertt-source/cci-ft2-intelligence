"""
محول الملفات الخام إلى تنسيق FT2
"""
import os
import csv
import logging
import shutil
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_csv_to_ft2(csv_path: str, output_path: str):
    """
    تحويل ملف CSV إلى تنسيق FT2 نصي
    
    Args:
        csv_path: مسار ملف CSV المدخل
        output_path: مسار ملف FT2 المخرج
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f_in:
            # محاولة اكتشاف الفاصل تلقائياً
            try:
                sample = f_in.read(2048)
                f_in.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=[',', '\t', ';'])
                delimiter = dialect.delimiter
            except csv.Error:
                # العودة للافتراضي إذا فشل الاكتشاف
                f_in.seek(0)
                delimiter = '\t' if csv_path.lower().endswith('.tsv') else ','
            
            reader = csv.DictReader(f_in, delimiter=delimiter)
            rows = list(reader)
        
        if not rows:
            logger.warning(f"ملف CSV فارغ: {csv_path}")
            return
        
        # إنشاء محتوى FT2
        ft2_content = []
        
        # رأس FT2
        ft2_content.append("Device: Q-tag Fridge-tag 2 E")
        ft2_content.append("Vers: 0.5")
        ft2_content.append(f"Serial: {rows[0].get('device_id', 'UNKNOWN')}")
        ft2_content.append("Temp unit: C")
        ft2_content.append("Alarm:")
        ft2_content.append("  0:")
        ft2_content.append("   T AL: -0.5, t AL: 60")
        ft2_content.append("  1:")
        ft2_content.append("   T AL: +8.0, t AL: 600")
        ft2_content.append("Hist:")
        
        # إضافة البيانات
        for i, row in enumerate(rows, 1):
            try:
                # تنظيف أسماء الأعمدة من المسافات الزائدة إذا وجدت
                row = {k.strip(): v for k, v in row.items() if k}
                
                ts_str = row.get('timestamp', '').strip().replace(' ', 'T')
                
                if not ts_str:
                    logger.warning(f"تخطي صف {i} في {csv_path}: حقل timestamp مفقود أو فارغ")
                    continue

                date_str = datetime.fromisoformat(ts_str).strftime('%Y-%m-%d')
                temp = float(row.get('temperature', 0))
                
                ft2_content.append(f" {i}:")
                ft2_content.append(f"  Date: {date_str}")
                ft2_content.append(f"  Min T: {temp:.1f}")
                ft2_content.append(f"  Max T: {temp:.1f}")
                ft2_content.append(f"  Avrg T: {temp:.1f}")
                ft2_content.append(f"  Alarm:")
                ft2_content.append(f"   0:")
                ft2_content.append(f"    t Acc: {0 if temp > -0.5 else 60}")
                ft2_content.append(f"   1:")
                ft2_content.append(f"    t Acc: {60 if temp > 8.0 else 0}")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"تخطي صف {i} في {csv_path}: {e}")
                continue
        
        # حفظ الملف
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write('\n'.join(ft2_content))
        
        logger.info(f"تم تحويل {csv_path} إلى {output_path} ({len(rows)} صف)")
        
    except Exception as e:
        logger.error(f"خطأ في تحويل {csv_path}: {e}")

def convert_all_files(input_dir: str, output_dir: str):
    """
    تحويل جميع الملفات في المجلد إلى تنسيق FT2
    
    Args:
        input_dir: مجلد الملفات المدخلة
        output_dir: مجلد الملفات المخرجة
    """
    os.makedirs(output_dir, exist_ok=True)
    
    converted_count = 0
    
    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)
        output_filename = os.path.splitext(filename)[0] + '.txt'
        output_path = os.path.join(output_dir, output_filename)
        
        # التحقق مما إذا كان الملف هو نفسه لتجنب الكتابة فوقه وتلف البيانات
        is_same_file = os.path.abspath(input_path) == os.path.abspath(output_path)

        if filename.endswith('.txt'):
            if not is_same_file:
                try:
                    shutil.copy2(input_path, output_path)
                    logger.info(f"تم نسخ الملف النصي: {filename}")
                except Exception as e:
                    logger.error(f"فشل نسخ {filename}: {e}")
        
        elif filename.endswith(('.csv', '.tsv')):
            try:
                convert_csv_to_ft2(input_path, output_path)
                converted_count += 1
            except Exception as e:
                logger.error(f"فشل تحويل {filename}: {e}")
    
    logger.info(f"تم تحويل {converted_count} ملف إلى تنسيق FT2")