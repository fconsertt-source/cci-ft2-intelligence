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
from src.infrastructure.logging import get_logger
from src.shared.di_container import create_evaluate_cold_chain_uc
from src.infrastructure.adapters.ft2_reader_adapter import FT2ReaderAdapter
from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.evaluate_cold_chain_safety_request import EvaluateColdChainSafetyRequest, TemperatureReading
from src.application.use_cases.evaluate_cold_chain_safety_use_case import EvaluateColdChainSafetyUseCase
from scripts.create_test_data import create_test_data
from src.domain.services.rules_engine import calculate_center_stats
from src.presentation.reporting.csv_reporter import generatecgenerate_centers_report, MessageProvider



logger = get_logger(__name__)

# --- Phase 2: Runtime Entity Proxy ---
# نستخدم هذا الكلاس بدلاً من DTO أثناء المعالجة لضمان وجود الإعدادات (temperature_ranges)
# التي يحتاجها محرك القواعد. يتم التحويل إلى DTO فقط عند التقرير.
class RuntimeCenter:
    def __init__(self, id, name, device_ids, temperature_ranges=None, decision_thresholds=None):
        self.id = id
        self.name = name
        self.device_ids = device_ids
        self.temperature_ranges = temperature_ranges or {'min': 2.0, 'max': 8.0}
        self.decision_thresholds = decision_thresholds or {}
        self.ft2_entries = []
        
        # حقول النتائج
        self.decision = 'UNKNOWN'
        self.vvm_stage = 'NONE'
        self.alert_level = None
        self.stability_budget_consumed_pct = 0.0
        self.thaw_remaining_hours = None
        self.category_display = None
        self.decision_reasons = []

    def add_ft2_entry(self, entry):
        self.ft2_entries.append(entry)


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

def load_centers(config_path: str = "config/center_profiles.yaml") -> List:
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
            
            # Phase 2 Fix: استخدام RuntimeCenter بدلاً من DTO للحفاظ على الإعدادات
            try:
                # profile is expected to be a dict from YAML
                device_ids = profile.get('device_ids', []) if isinstance(profile, dict) else getattr(profile, 'device_ids', [])
                center_id = profile.get('id', profile.get('center_id')) if isinstance(profile, dict) else getattr(profile, 'id', None)
                name = profile.get('name', '') if isinstance(profile, dict) else getattr(profile, 'name', '')
                temp_ranges = profile.get('temperature_ranges') if isinstance(profile, dict) else getattr(profile, 'temperature_ranges', None)
                thresholds = profile.get('decision_thresholds') if isinstance(profile, dict) else getattr(profile, 'decision_thresholds', None)

                rc = RuntimeCenter(
                    id=center_id,
                    name=name,
                    device_ids=device_ids,
                    temperature_ranges=temp_ranges,
                    decision_thresholds=thresholds
                )
                centers.append(rc)
            except Exception:
                centers.append(profile)

        logger.info(f"تم تحميل {len(centers)} مركز تطعيم (Entities/Profiles)")
        return centers
    except Exception as e:
        logger.critical(MessageProvider.get('CRITICAL_CONFIG_LOAD_FAILED', error=e))
        # تحسين الصمود: عدم استخدام قيم افتراضية في الأنظمة الطبية
        raise RuntimeError(MessageProvider.get('CONFIG_LOAD_FAILED_STOP')) from e



def process_ft2_file_new(file_path: str, centers: list, device_map: Dict[str, object] = None) -> Optional[dict]:
    """
    معالجة ملف FT2 باستخدام النظام الجديد
    
    Returns:
        dict: نتائج التحليل
    """
    try:
        logger.info(f"🔍 معالجة الملف (نظام جديد): {os.path.basename(file_path)}")
        
        # استخدام النظام الجديد عبر الـ Adapter والـ Use Case
        # هذا الدّور الآن يُعهد إلى Use Case التي تتلقى Reader Adapter
        # (التحويل الكامل إلى DTOs يحدث تدريجيًا عبر المappers)
        reader = FT2ReaderAdapter()
        entries = reader.read_all()

        # أثناء المرحلة المرحلية، سنبقي الربط القديم كقيمة احتياطية
        try:
            from src.infrastructure.ft2_reader.services.ft2_linker import FT2Linker
            FT2Linker.link(entries, centers)
        except Exception:
            pass
        
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
                
                # 1. تطبيق القواعد لتحديث القرار
                apply_rules(center)
                
                # 2. الحصول على الإحصائيات للتقرير
                stats = calculate_center_stats(center)

                center_analysis = {
                    'center_id': center.id,
                    'center_name': center.name,
                    'entries_count': len(center.ft2_entries),
                    'decision': center.decision,
                    'has_freeze': stats['has_freeze'],
                    'has_ccm_violation': stats['has_ccm_violation']
                }
                analysis['centers_affected'].append(center_analysis)
        
        logger.info(f"✅ تم معالجة {len(entries)} إدخال لـ {len(analysis['centers_affected'])} مركز")
        
        return analysis
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الملف {file_path}: {e}")
        return None

def run_pipeline(config_path: str = "config/center_profiles.yaml", 
                 input_dir: str = "data/input_raw",
                 output_dir: str = "data/output"):
    """تشغيل خط المعالجة الكامل"""
    
    logger.info(MessageProvider.get('PIPELINE_START'))
    
    # 1. إعداد المجلدات
    setup_directories()
    
    # 2. تحميل مراكز التطعيم
    centers = load_centers(config_path)
    
    # تحسين الأداء: إنشاء خريطة البحث السريع (Hash Map) للأجهزة
    # التعقيد: O(1) للبحث بدلاً من O(N)
    device_map = {}
    for center in centers:
        device_ids = getattr(center, 'device_ids', []) if not isinstance(center, dict) else center.get('device_ids', [])
        for device_id in device_ids:
            device_map[device_id] = center
    
    # 3. تحويل الملفات الخام (إذا كانت موجودة)
    ft2_files = []
    ft2_dir = ""

    # النظام الجديد يعالج ملفات CSV/TSV مباشرة
    ft2_dir = input_dir
    if os.path.exists(ft2_dir):
        ft2_files = [f for f in os.listdir(ft2_dir) if f.endswith(('.csv', '.tsv'))]
            
    if not ft2_files:
        logger.warning(MessageProvider.get('NO_FILES_TO_PROCESS', path=ft2_dir))
        
        # اقتراح ذكي للمستخدم
        if not os.listdir(input_dir):
            logger.info(MessageProvider.get('EMPTY_INPUT_DIR_HINT'))
        return

    logger.info(MessageProvider.get('FILES_FOUND_TO_PROCESS', count=len(ft2_files), path=ft2_dir))
    
    failed_files = []
    
    # --- الإصلاح المعماري ---
    # إزالة حالة الاستخدام (Use Case) والعودة إلى منطق التحليل والربط البسيط
    # الذي يتوافق مع بنية البرنامج النصي.
    from src.infrastructure.ft2_reader.parser.ft2_parser import FT2Parser
    from src.infrastructure.ft2_reader.services.ft2_linker import FT2Linker

    for ft2_file in ft2_files:
        ft2_path = os.path.join(ft2_dir, ft2_file)
        try:
            # 1. التحليل (Parse)
            entries = FT2Parser.parse_file(ft2_path)

            # 2. الربط (Link)
            # FT2Linker expects objects with `device_ids` and `add_ft2_entry`.
            # RuntimeCenter now implements add_ft2_entry directly.
            FT2Linker.link(entries, centers)

            logger.info(f"✅ تمت معالجة وربط: {ft2_file}")
        except Exception as e:
            logger.error(MessageProvider.get('FILE_PROCESSING_FAILED', file=ft2_file, error=e))
            failed_files.append((ft2_file, str(e)))
    
    # 5. تطبيق القواعد وإنشاء التقارير (عبر UseCase)
    logger.info(" Applying rules via EvaluateColdChainSafetyUseCase...")
    
    # Instantiate UseCase (Pure Logic, no readers)
    use_case = EvaluateColdChainSafetyUseCase()
    
    all_results = [] # للتوافق مع بنية التقرير القديمة
    for center in centers:
        if center.ft2_entries:
            # 1. Prepare Request (Data Only)
            readings = tuple(
                TemperatureReading(
                    value=entry.temp,
                    timestamp=entry.timestamp,
                    device_id=getattr(entry, 'device_id', 'unknown')
                ) for entry in center.ft2_entries
            )
            
            request = EvaluateColdChainSafetyRequest(
                center_id=center.id,
                center_name=center.name,
                readings=readings,
                temperature_ranges=center.temperature_ranges,
                decision_thresholds=center.decision_thresholds
            )
            
            # 2. Execute UseCase (Pure Processing)
            response = use_case.execute(request)
            
            # 3. Update Runtime Object with Results (for reporting compatibility)
            center.decision = response.decision
            center.vvm_stage = response.vvm_stage
            center.alert_level = response.alert_level
            center.stability_budget_consumed_pct = response.stability_budget_consumed_pct
            center.thaw_remaining_hours = response.thaw_remaining_hours
            center.category_display = response.category_display
            center.decision_reasons = list(response.decision_reasons)
            
            all_results.append({'file_path': 'Multiple sources', 'centers_affected': [{'center_name': center.name, 'entries_count': len(center.ft2_entries)}]})

    # --- Phase 2: Mapping Boundary ---
    # تحويل RuntimeCenter إلى CenterDTO قبل التقرير
    # هذا يضمن أن طبقة التقرير لا تتعامل مع كائنات المجال أو الكائنات المؤقتة
    center_dtos = []
    for c in centers:
        dto = CenterDTO(
            id=c.id,
            name=c.name,
            device_ids=c.device_ids,
            ft2_entries=c.ft2_entries,
            decision=c.decision,
            vvm_stage=c.vvm_stage,
            alert_level=c.alert_level,
            stability_budget_consumed_pct=c.stability_budget_consumed_pct,
            thaw_remaining_hours=c.thaw_remaining_hours,
            category_display=c.category_display,
            decision_reasons=c.decision_reasons
        )
        center_dtos.append(dto)

    # تقرير المراكز
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(center_dtos, centers_report_path)
    
    # التقارير التفصيلية (تم تبسيطها لأن الربط شامل)
    reports_dir = os.path.join(output_dir, "detailed_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 6. عرض الملخص
    logger.info("%s", "\n" + ("="*70))
    logger.info(MessageProvider.get('PIPELINE_SUMMARY_TITLE'))
    logger.info("%s", "="*70)
    logger.info(MessageProvider.get('FILES_PROCESSED', processed_count=len(all_results), total_count=len(ft2_files)))
    logger.info(MessageProvider.get('FILES_FAILED', failed_count=len(failed_files)))
    logger.info(MessageProvider.get('CENTER_REPORT_GENERATED', path=centers_report_path))
    logger.info(MessageProvider.get('DETAILED_REPORTS_GENERATED', path=f"{reports_dir}/"))

    if failed_files:
        logger.warning(MessageProvider.get('FAILED_FILES_LIST_TITLE'))
        for file, error in failed_files:
            logger.warning("  - %s: %s", file, error)
    
    logger.info(MessageProvider.get('PIPELINE_COMPLETE', output_dir=output_dir))

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description=MessageProvider.get('CLI_DESCRIPTION'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s                           # التشغيل الافتراضي
  %(prog)s --config my_config.yaml   # استخدام تكوين مخصص
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
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='عرض معلومات تفصيلية')
    parser.add_argument('--generate-data', action='store_true', dest='generate_data', help='إنشاء بيانات اختبار في data/input_raw')
    
    args = parser.parse_args()
    
    # ضبط مستوى التسجيل
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")
    
    try:
        if getattr(args, 'generate_data', False):
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()

        run_pipeline(
            config_path=args.config,
            input_dir=args.input,
            output_dir=args.output
        )
    except Exception as e:
        logger.error(MessageProvider.get('UNEXPECTED_ERROR', error=e))
        sys.exit(1)

if __name__ == "__main__":
    main()