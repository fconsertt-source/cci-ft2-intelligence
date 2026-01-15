# scripts/run_ft2_pipeline.py
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.yaml_loader import load_yaml
from src.ft2_reader.parser.ft2_parser import FT2Parser, FT2Entry
from src.ft2_reader.validator.ft2_validator import FT2Validator
from src.ft2_reader.services.ft2_linker import FT2Linker
from src.core.entities.vaccination_center import VaccinationCenter
from scripts.create_test_data import create_test_data
from src.reporting.csv_reporter import generate_centers_report

# استيراد الوحدات القديمة بشكل آمن (Graceful Import)
# هذا يمنع توقف البرنامج إذا تم حذف المجلد src/ingestion مستقبلاً
try:
    from src.ingestion.ft2_converter import convert_all_files
    from src.ingestion.ft2_parser import FT2Parser as LegacyFT2Parser
except ImportError:
    convert_all_files = None
    LegacyFT2Parser = None
    # لا نقوم بطباعة تحذير هنا لتجنب إزعاج المستخدم إلا إذا حاول استخدام النظام القديم

# تحديد توفر النظام القديم بوضوح (Feature Flag)
LEGACY_AVAILABLE = LegacyFT2Parser is not None

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('pipeline.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """إعداد المجلدات المطلوبة"""
    directories = [
        'data/input_raw',
        'data/input_ft2',
        'data/output',
        'data/reports',
        'config'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"تم إنشاء/التحقق من المجلد: {directory}")

def load_centers(config_path: str = "config/center_profiles.yaml") -> List[VaccinationCenter]:
    """تحميل مراكز التطعيم من ملف التكوين"""
    try:
        center_profiles = load_yaml(config_path)
        centers = []
        for profile in center_profiles:
            # --- طبقة التوافق مع الملف المطور (Enhanced Profile Adapter) ---
            # إذا كان الملف يحتوي على ملفات تعريف حرارة متعددة (النظام الجديد)
            # نقوم بحساب النطاق العام (الأوسع) لضمان عمل الكلاس القديم
            if 'temperature_profiles' in profile and 'temperature_ranges' not in profile:
                temps = profile['temperature_profiles']
                # استخراج أقل حد أدنى وأعلى حد أقصى من جميع اللقاحات
                min_t = min((v['min'] for v in temps.values()), default=2)
                max_t = max((v['max'] for v in temps.values()), default=8)
                profile['temperature_ranges'] = {'min': min_t, 'max': max_t}
                # تنظيف الحقول غير المدعومة في الكلاس القديم لتجنب أخطاء __init__
                profile.pop('temperature_profiles', None)
                profile.pop('policies', None)
                profile.pop('reporting', None)
            
            centers.append(VaccinationCenter(**profile))
            
        logger.info(f"تم تحميل {len(centers)} مركز تطعيم")
        return centers
    except Exception as e:
        logger.critical(f"❌ خطأ حرج في تحميل تكوين المراكز: {e}")
        # تحسين الصمود: عدم استخدام قيم افتراضية في الأنظمة الطبية
        raise RuntimeError("فشل تحميل تكوين المراكز. تم إيقاف التشغيل لسلامة البيانات.") from e

def process_ft2_file_legacy(file_path: str, centers: list) -> Optional[dict]:
    """
    معالجة ملف FT2 باستخدام المحلل القديم (للتوافق)
    
    Returns:
        dict: نتائج التحليل
    """
    try:
        logger.info(f"🔍 معالجة الملف (نظام قديم): {os.path.basename(file_path)}")
        
        if not LEGACY_AVAILABLE:
            logger.error("❌ المحلل القديم غير متوفر (src.ingestion.ft2_parser مفقود)")
            return None

        # استخدام المحلل القديم
        parser = LegacyFT2Parser()
        data = parser.parse(file_path)
        
        if not data or not data.get('history'):
            logger.warning(f"لم يتم العثور على بيانات في الملف: {file_path}")
            return None
        
        # تحويل البيانات القديمة إلى كائنات FT2Entry لربطها بالمراكز
        device_id = data.get('device_info', {}).get('serial_number', 'UNKNOWN')
        entries = []
        
        for day in data.get('history', []):
            date_str = day.get('date')
            alarms = day.get('alarms', {})
            # إضافة إدخال للحد الأدنى (لكشف التجميد)
            if 'min_temp' in day:
                # التعامل مع المفاتيح سواء كانت نصوص أو أرقام
                entries.append(FT2Entry(
                    device_id=device_id,
                    timestamp=f"{date_str}T00:00:00", # وقت افتراضي
                    temperature=day['min_temp'],
                    vaccine_type="UNKNOWN",
                    batch="UNKNOWN",
                    duration_minutes=float(alarms.get('0', 0)) # زمن التجميد
                ))
            # إضافة إدخال للحد الأقصى (لكشف التعرض للحرارة)
            if 'max_temp' in day:
                entries.append(FT2Entry(
                    device_id=device_id,
                    timestamp=f"{date_str}T12:00:00", # وقت افتراضي
                    temperature=day['max_temp'],
                    vaccine_type="UNKNOWN",
                    batch="UNKNOWN",
                    duration_minutes=float(alarms.get('1', 0)) # زمن الحرارة
                ))
        
        # ربط البيانات بالمراكز
        FT2Linker.link(entries, centers)

        # تحليل النتائج
        analysis = {
            'device_info': data.get('device_info', {}),
            'file_path': file_path,
            'parsed_at': datetime.now().isoformat(),
            'history_summary': parser.get_summary() if hasattr(parser, 'get_summary') else {}
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الملف {file_path}: {e}")
        return None

def process_ft2_file_new(file_path: str, centers: list, device_map: Dict[str, VaccinationCenter] = None) -> Optional[dict]:
    """
    معالجة ملف FT2 باستخدام النظام الجديد
    
    Returns:
        dict: نتائج التحليل
    """
    try:
        logger.info(f"🔍 معالجة الملف (نظام جديد): {os.path.basename(file_path)}")
        
        # استخدام النظام الجديد
        entries = FT2Parser.parse_file(file_path)
        
        # تحسين الأداء: استخدام الخريطة إذا توفرت، وإلا البناء التقليدي
        if device_map:
            valid_device_ids = list(device_map.keys())
        else:
            valid_device_ids = []
            for center in centers:
                valid_device_ids.extend(center.device_ids)
        
        # التحقق من الصحة
        entries = FT2Validator.validate(entries, valid_device_ids)
        
        # ربط البيانات بالمراكز
        FT2Linker.link(entries, centers)
        
        # تحليل النتائج لكل مركز
        analysis = {
            'file_path': file_path,
            'parsed_at': datetime.now().isoformat(),
            'entries_count': len(entries),
            'centers_affected': [],
            'analysis': {}
        }
        
        # تحديد الأجهزة الموجودة في الملف الحالي لتصفية التقرير
        current_file_device_ids = set(entry.device_id for entry in entries)
        affected_centers = set()

        # تحسين الأداء: البحث المباشر باستخدام الخريطة O(1) بدلاً من الحلقات المتداخلة
        if device_map:
            for device_id in current_file_device_ids:
                if device_id in device_map:
                    affected_centers.add(device_map[device_id])
        else:
            # الطريقة القديمة (للاحتياط)
            for center in centers:
                if any(d_id in current_file_device_ids for d_id in center.device_ids):
                    affected_centers.add(center)
        
        # تجميع النتائج
        for center in affected_centers:
            if center.ft2_entries: # التأكد من وجود بيانات مرتبطة
                center_analysis = {
                    'center_id': center.id,
                    'center_name': center.name,
                    'entries_count': len(center.ft2_entries),
                    'decision': center.decision,
                    'has_freeze': any(e.temperature < -0.5 for e in center.ft2_entries),
                    'has_ccm_violation': any(e.temperature > 8.0 for e in center.ft2_entries)
                }
                analysis['centers_affected'].append(center_analysis)
        
        logger.info(f"✅ تم معالجة {len(entries)} إدخال لـ {len(analysis['centers_affected'])} مركز")
        
        return analysis
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الملف {file_path}: {e}")
        return None

def run_pipeline(config_path: str = "config/center_profiles.yaml", 
                 input_dir: str = "data/input_raw",
                 output_dir: str = "data/output",
                 use_legacy: bool = False):
    """تشغيل خط المعالجة الكامل"""
    
    logger.info("🚀 بدء تشغيل خط معالجة FT2")
    
    # 1. إعداد المجلدات
    setup_directories()
    
    # 2. تحميل مراكز التطعيم
    centers = load_centers(config_path)
    
    # تحسين الأداء: إنشاء خريطة البحث السريع (Hash Map) للأجهزة
    # التعقيد: O(1) للبحث بدلاً من O(N)
    device_map = {device_id: center for center in centers for device_id in center.device_ids}
    
    # 3. تحويل الملفات الخام (إذا كانت موجودة)
    ft2_files = []
    ft2_dir = ""

    if use_legacy:
        # النظام القديم يتوقع ملفات نصية محولة
        if os.path.exists(input_dir) and os.listdir(input_dir):
            if not convert_all_files:
                logger.error("❌ أداة التحويل القديمة غير متوفرة (src.ingestion.ft2_converter مفقود)")
                return

            logger.info("🔄 تحويل الملفات الخام إلى تنسيق FT2 (Legacy)")
            convert_all_files(input_dir, "data/input_ft2")
        
        ft2_dir = "data/input_ft2"
        if os.path.exists(ft2_dir):
            ft2_files = [f for f in os.listdir(ft2_dir) if f.endswith('.txt')]
    else:
        # النظام الجديد يعالج ملفات CSV/TSV مباشرة
        ft2_dir = input_dir
        if os.path.exists(ft2_dir):
            ft2_files = [f for f in os.listdir(ft2_dir) if f.endswith(('.csv', '.tsv'))]
            
    if not ft2_files:
        logger.warning(f"⚠️ لم يتم العثور على ملفات للمعالجة في: {ft2_dir}")
        
        # اقتراح ذكي للمستخدم إذا وجدت ملفات في المجلد القديم
        if not use_legacy and os.path.exists("data/input_ft2") and any(f.endswith('.txt') for f in os.listdir("data/input_ft2")):
            logger.info("💡 تلميح: تم العثور على ملفات نصية في data/input_ft2. جرب التشغيل مع خيار --legacy")
        elif not os.listdir(input_dir):
            logger.info("💡 تلميح: المجلد فارغ. يمكنك إنشاء بيانات اختبار باستخدام الخيار: --generate-data")
        return

    logger.info(f"📁 وجد {len(ft2_files)} ملف للمعالجة في {ft2_dir}")
    
    failed_files = []
    all_results = []
    
    for ft2_file in ft2_files:
        ft2_path = os.path.join(ft2_dir, ft2_file)
        
        try:
            # اختيار نظام المعالجة
            if use_legacy:
                result = process_ft2_file_legacy(ft2_path, centers)
            else:
                result = process_ft2_file_new(ft2_path, centers, device_map)
            
            if result:
                all_results.append(result)
                logger.info(f"✅ تمت معالجة: {ft2_file}")
            else:
                failed_files.append((ft2_file, "فشل التحليل"))
                
        except Exception as e:
            logger.error(f"❌ فشل معالجة {ft2_file}: {e}")
            failed_files.append((ft2_file, str(e)))
    
    # 5. إنشاء التقارير
    logger.info("📊 إنشاء التقارير...")
    
    # تقرير المراكز
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(centers, centers_report_path)
    
    # التقارير التفصيلية
    reports_dir = os.path.join(output_dir, "detailed_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    for i, result in enumerate(all_results):
        report_path = os.path.join(reports_dir, f"report_{i+1:03d}.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"تقرير تحليل FT2\n")
            f.write(f"================\n\n")
            f.write(f"الملف: {result.get('file_path', 'غير معروف')}\n")
            f.write(f"وقت التحليل: {result.get('parsed_at', 'غير معروف')}\n\n")
            
            if 'device_info' in result:
                f.write(f"معلومات الجهاز:\n")
                for key, value in result['device_info'].items():
                    f.write(f"  {key}: {value}\n")
            
            if 'centers_affected' in result:
                f.write(f"\nالمراكز المتأثرة:\n")
                for center in result['centers_affected']:
                    f.write(f"  - {center['center_name']}: {center['entries_count']} إدخال\n")
    
    # 6. عرض الملخص
    print(f"\n{'='*70}")
    print("ملخص تشغيل خط المعالجة")
    print(f"{'='*70}")
    print(f"الملفات المعالجة: {len(all_results)} من أصل {len(ft2_files)}")
    print(f"الملفات الفاشلة: {len(failed_files)}")
    print(f"تقرير المراكز: {centers_report_path}")
    print(f"التقارير التفصيلية: {reports_dir}/")
    
    if failed_files:
        print(f"\nالملفات الفاشلة:")
        for file, error in failed_files:
            print(f"  - {file}: {error}")
    
    print(f"{'='*70}")
    
    logger.info(f"🏁 اكتمل خط المعالجة. انظر {output_dir} للنتائج")

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description='نظام متكامل لمعالجة ملفات FT2 لمراقبة سلسلة التبريد',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s                           # التشغيل الافتراضي
  %(prog)s --config my_config.yaml   # استخدام تكوين مخصص
  %(prog)s --legacy                  # استخدام نظام المعالجة القديم
  %(prog)s --input ./my_data         # مجلد بيانات مخصص
  %(prog)s --verbose                 # عرض تفاصيل أكثر
        """
    )
    
    parser.add_argument('--config', '-c', default='config/center_profiles.yaml',
                       help='مسار ملف تكوين المراكز')
    parser.add_argument('--input', '-i', default='data/input_raw',
                       help='مجلد الملفات الخام المدخلة')
    parser.add_argument('--output', '-o', default='data/output',
                       help='مجلد الملفات المخرجة')
    parser.add_argument('--legacy', '-l', action='store_true',
                       help='استخدام نظام المعالجة القديم (للتوافق)')
    parser.add_argument('--generate-data', '-g', action='store_true',
                       help='إنشاء بيانات اختبار جديدة قبل بدء المعالجة')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='عرض معلومات تفصيلية')
    
    args = parser.parse_args()
    
    # ضبط مستوى التسجيل
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")
    
    try:
        if args.generate_data:
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()

        run_pipeline(
            config_path=args.config,
            input_dir=args.input,
            output_dir=args.output,
            use_legacy=args.legacy
        )
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()