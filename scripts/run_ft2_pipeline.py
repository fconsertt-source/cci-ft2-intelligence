# scripts/run_ft2_pipeline.py
import argparse
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from scripts.create_test_data import create_test_data
from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, TemperatureReading)
from src.application.use_cases.evaluate_cold_chain_safety_use_case import \
    EvaluateColdChainSafetyUseCase
from src.domain.enums.vaccine_decision import VaccineDecision
from src.domain.services.judgment_engine import JudgmentEngine
from src.domain.services.rules_engine import (apply_rules,
                                              calculate_center_stats)
from src.infrastructure.adapters.ft2_reader_adapter import FT2ReaderAdapter
from src.infrastructure.logging import get_logger
from src.infrastructure.utils.yaml_loader import load_yaml
from src.presentation.messages.message_map import MessageProvider
from src.presentation.reporting.csv_reporter import generate_centers_report

logger = get_logger(__name__)


# --- Phase 2: Runtime Entity Proxy ---
# نستخدم هذا الكلاس بدلاً من DTO أثناء المعالجة لضمان وجود الإعدادات (temperature_ranges)
# التي يحتاجها محرك القواعد. يتم التحويل إلى DTO فقط عند التقرير.
class RuntimeCenter:
    def __init__(
        self, id, name, device_ids, temperature_ranges=None, decision_thresholds=None
    ):
        self.id = id
        self.name = name
        self.device_ids = device_ids
        self.temperature_ranges = temperature_ranges or {"min": 2.0, "max": 8.0}
        self.decision_thresholds = decision_thresholds or {}
        self.ft2_entries = []

        # حقول النتائج
        self.decision = "UNKNOWN"
        self.vvm_stage = "NONE"
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
        "data/input_raw",
        "data/input_ft2",
        "data/output",
        "data/reports",
        "config",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug("تم إنشاء/التحقق من المجلد: %s", directory)


def validate_input_directory(input_dir: str) -> bool:
    """
    التحقق من أن مسار الإدخال موجود وهو مجلد.
    إذا كان موجوداً ولكنه ملف، يتم تسجيل خطأ والخروج.
    """
    if not os.path.exists(input_dir):
        logger.error("❌ المسار %s غير موجود.", input_dir)
        return False
    if not os.path.isdir(input_dir):
        logger.error("❌ المسار %s موجود ولكنه ليس مجلداً (ربما هو ملف).", input_dir)
        logger.error("    الرجاء تحديد مجلد يحتوي على ملفات .csv أو .tsv.")
        return False
    return True


def load_centers(
    config_path: str = "config/center_profiles.yaml",
) -> List[RuntimeCenter]:
    """تحميل مراكز التطعيم من ملف التكوين"""
    try:
        data = load_yaml(config_path)
        # إذا كان الملف يحتوي على مفتاح 'centers'، نستخرج قائمة المراكز
        if isinstance(data, dict) and "centers" in data:
            centers_dict = data["centers"]
        else:
            centers_dict = data

        # إذا كانت البيانات ليست قاموساً أو قائمة، نخرج خطأ
        if not isinstance(centers_dict, dict):
            logger.error("❌ تنسيق YAML غير صحيح: توقع قاموس (dict) للمراكز")
            return []

        centers = []
        for center_id, profile in centers_dict.items():
            # profile هو قاموس الخصائص
            if not isinstance(profile, dict):
                logger.warning(f"⚠️ الإدخال '{center_id}' ليس قاموساً، يتم تخطيه")
                continue

            # استخراج الحقول
            name = profile.get("name", f"مركز {center_id}")
            device_ids = profile.get("device_ids", [])
            # التأكد من أن device_ids قائمة
            if not isinstance(device_ids, list):
                device_ids = []

            # نطاقات الحرارة
            temp_ranges = profile.get("temperature_ranges")
            # إذا كان هناك "temperature_profiles" (النظام الجديد) نحسب النطاق الأوسع
            if "temperature_profiles" in profile and not temp_ranges:
                temps = profile["temperature_profiles"]
                min_t = min((v["min"] for v in temps.values()), default=2.0)
                max_t = max((v["max"] for v in temps.values()), default=8.0)
                temp_ranges = {"min": min_t, "max": max_t}

            thresholds = profile.get("decision_thresholds")

            # إنشاء كائن RuntimeCenter
            rc = RuntimeCenter(
                id=center_id,
                name=name,
                device_ids=device_ids,
                temperature_ranges=temp_ranges,
                decision_thresholds=thresholds,
            )
            centers.append(rc)

        logger.info(f"تم تحميل {len(centers)} مركز تطعيم (Entities/Profiles)")
        return centers

    except Exception as e:
        logger.critical(f"فشل تحميل التكوين: {e}")
        raise RuntimeError("فشل تحميل إعدادات المراكز") from e


def process_ft2_file_new(
    file_path: str, centers: list, device_map: Dict[str, object] = None
) -> Optional[dict]:
    """
    معالجة ملف FT2 باستخدام النظام الجديد

    Returns:
        dict: نتائج التحليل
    """
    try:
        logger.info("🔍 معالجة الملف (نظام جديد): %s", os.path.basename(file_path))

        # استخدام النظام الجديد عبر الـ Adapter والـ Use Case
        # هذا الدّور الآن يُعهد إلى Use Case التي تتلقى Reader Adapter
        # (التحويل الكامل إلى DTOs يحدث تدريجيًا عبر المappers)
        reader = FT2ReaderAdapter()
        entries = reader.read_all()

        # أثناء المرحلة المرحلية، سنبقي الربط القديم كقيمة احتياطية
        try:
            from src.infrastructure.ft2_reader.services.ft2_linker import \
                FT2Linker

            FT2Linker.link(entries, centers)
        except Exception:
            pass

        # تحليل النتائج لكل مركز
        analysis = {
            "file_path": file_path,
            "parsed_at": datetime.now().isoformat(),
            "entries_count": len(entries),
            "centers_affected": [],
            "analysis": {},
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
            if center.ft2_entries:  # التأكد من وجود بيانات مرتبطة

                # 1. تطبيق القواعد لتحديث القرار
                apply_rules(center)

                # 2. الحصول على الإحصائيات للتقرير
                stats = calculate_center_stats(center)

                center_analysis = {
                    "center_id": center.id,
                    "center_name": center.name,
                    "entries_count": len(center.ft2_entries),
                    "decision": center.decision,
                    "has_freeze": stats["has_freeze"],
                    "has_ccm_violation": stats["has_ccm_violation"],
                }
                analysis["centers_affected"].append(center_analysis)

        logger.info(
            f"✅ تم معالجة {len(entries)} إدخال لـ {len(analysis['centers_affected'])} مركز"
        )

        return analysis

    except Exception as e:
        logger.error("❌ خطأ في معالجة الملف %s: %s", file_path, e)
        return None


def run_pipeline(
    config_path: str = "config/center_profiles.yaml",
    input_dir: str = "data/input_raw",
    output_dir: str = "data/output",
):
    """تشغيل خط المعالجة الكامل"""

    logger.info(MessageProvider.get("PIPELINE_START"))

    # 1. إعداد المجلدات
    setup_directories()

    # 2. تحميل مراكز التطعيم
    centers = load_centers(config_path)

    use_case = EvaluateColdChainSafetyUseCase()

    # تحسين الأداء: إنشاء خريطة البحث السريع (Hash Map) للأجهزة
    # التعقيد: O(1) للبحث بدلاً من O(N)
    device_map = {}
    for center in centers:
        device_ids = (
            getattr(center, "device_ids", [])
            if not isinstance(center, dict)
            else center.get("device_ids", [])
        )
        for device_id in device_ids:
            device_map[device_id] = center

    # 3. التحقق من صحة مجلد الإدخال قبل المعالجة
    if not validate_input_directory(input_dir):
        logger.error("❌ فشل التحقق من مجلد الإدخال. إنهاء التنفيذ.")
        sys.exit(1)

    # 4. الحصول على قائمة الملفات
    ft2_files = []
    ft2_dir = input_dir
    logger.debug("فحص محتويات المجلد: %s", ft2_dir)
    try:
        all_items = os.listdir(ft2_dir)
        logger.debug("الملفات الموجودة: %s", all_items)
        ft2_files = [f for f in all_items if f.endswith((".csv", ".tsv", ".txt"))]
        logger.info(
            "تم العثور على %d ملف(ات) .csv/.tsv/.txt في %s", len(ft2_files), ft2_dir
        )
    except NotADirectoryError:
        logger.error("❌ المسار %s ليس مجلداً (NotADirectoryError).", ft2_dir)
        logger.error("تأكد من أن --input يشير إلى مجلد وليس ملف.")
        logger.debug(traceback.format_exc())
        sys.exit(1)
    except PermissionError as e:
        logger.error("❌ لا توجد صلاحية لقراءة المجلد %s: %s", ft2_dir, e)
        sys.exit(1)
    except Exception as e:
        logger.error("❌ خطأ غير متوقع أثناء قراءة المجلد %s: %s", ft2_dir, e)
        logger.debug(traceback.format_exc())
        sys.exit(1)

    if not ft2_files:
        logger.warning(MessageProvider.get("NO_FILES_TO_PROCESS", path=ft2_dir))

        # اقتراح ذكي للمستخدم
        if not os.listdir(input_dir):
            logger.info(MessageProvider.get("EMPTY_INPUT_DIR_HINT"))
        return

    logger.info(
        MessageProvider.get(
            "FILES_FOUND_TO_PROCESS", count=len(ft2_files), path=ft2_dir
        )
    )

    failed_files = []

    # --- الإصلاح المعماري ---
    # إزالة حالة الاستخدام (Use Case) والعودة إلى منطق التحليل والربط البسيط
    # الذي يتوافق مع بنية البرنامج النصي.
    from src.infrastructure.adapters.berlinger_ft2_reader import \
        BerlingerFt2Reader

    for ft2_file in ft2_files:
        ft2_path = os.path.join(ft2_dir, ft2_file)
        try:
            # تسجيل مسار الملف ونوعه للتحقق
            logger.debug("محاولة معالجة الملف: %s", ft2_path)
            if not os.path.isfile(ft2_path):
                logger.error("❌ المسار %s ليس ملفاً (تم تخطيه)", ft2_path)
                failed_files.append((ft2_file, "Not a file"))
                continue

            # 1. التحليل (Parse) - دعم FT2 و CSV المعالج
            if "_processed.csv" in ft2_file.lower():
                from src.infrastructure.adapters.processed_csv_reader import \
                    ProcessedCsvReader

                reader = ProcessedCsvReader()
                entries = reader.read(ft2_path)
            else:
                reader = BerlingerFt2Reader()
                entries = reader.read(ft2_path)

            device_ids_found = set(entry.device_id for entry in entries)
            logger.debug(f"🔍 الأجهزة المستخرجة من الملف: {device_ids_found}")

            # 2. الربط (Link) - يدوي للتحكم الكامل
            linked_count = 0
            skipped_count = 0

            for entry in entries:
                entry_device_id = getattr(entry, "device_id", None)
                if not entry_device_id:
                    skipped_count += 1
                    continue

                # البحث عن المركز المناسب
                found_center = False
                for center in centers:
                    if entry_device_id in center.device_ids:
                        center.add_ft2_entry(entry)
                        linked_count += 1
                        found_center = True
                        break

                if not found_center:
                    skipped_count += 1

            logger.info(f"✅ تم ربط {linked_count} إدخال، تم تخطي {skipped_count}")

        except Exception as e:
            logger.error("❌ خطأ في معالجة الملف %s: %s", ft2_file, e)
            logger.debug(traceback.format_exc())
            failed_files.append((ft2_file, str(e)))

    all_results = []  # للتوافق مع بنية التقرير القديمة
    for center in centers:
        if center.ft2_entries:
            # 1. Prepare Request (Data Only)
            readings = tuple(
                TemperatureReading(
                    value=entry.temperature,  # ← التغيير هنا
                    timestamp=entry.timestamp,
                    device_id=getattr(entry, "device_id", "unknown"),
                )
                for entry in center.ft2_entries
            )

            request = EvaluateColdChainSafetyRequest(
                center_id=center.id,
                center_name=center.name,
                readings=readings,
                temperature_ranges=center.temperature_ranges,
                decision_thresholds=center.decision_thresholds,
            )

            # 2. Execute UseCase (Pure Processing)
            # 2. Execute UseCase (Pure Processing)
            response = use_case.execute(request)

            # ✅ حساب CCM و HER
            her_ratio = getattr(response, "her_ratio", 0.0)
            ccm_index = getattr(response, "ccm_index", "0")
            has_freeze = getattr(response, "has_freeze", False)
            has_critical_heat = getattr(response, "has_critical_heat", False)

            # ✅ إنشاء JudgmentEngine
            judgment_engine = JudgmentEngine()
            decision_enum = _map_decision_to_vaccine_decision(response.decision)

            judgment = judgment_engine.judge(
                decision=decision_enum,
                decision_reason=(
                    " | ".join(response.decision_reasons)
                    if response.decision_reasons
                    else response.decision
                ),
                her_ratio=her_ratio,
                ccm_index=ccm_index,
                freeze_detected=has_freeze,
                has_critical_heat=has_critical_heat,
            )

            # ✅ تخزين جميع البيانات في stats
            center.stats = {
                "has_freeze": response.has_freeze,
                "has_ccm_violation": response.has_ccm_violation,
                "her_ratio": her_ratio,
                "ccm_index": ccm_index,
                "judgment_risk": judgment.risk_level,
                "judgment_narrative": judgment.narrative,
                "judgment_icon": judgment.risk_icon,
                "confidence": judgment.confidence,
                "requires_review": judgment.requires_human_review,
                "her_percentage": judgment.her_percentage,
            }

            # ✅ Logging علمي
            logger.info(
                f"Center {center.id}: "
                f"HER={judgment.her_percentage:.1f}% | "
                f"CCM={ccm_index} | "
                f"Decision={response.decision} | "
                f"Risk={judgment.risk_level} | "
                f"Confidence={judgment.confidence:.2f} | "
                f"Review={'Yes' if judgment.requires_human_review else 'No'}"
            )

            # 3. Update Runtime Object with Results (for reporting compatibility)
            center.decision = response.decision
            center.vvm_stage = response.vvm_stage
            center.alert_level = response.alert_level
            center.stability_budget_consumed_pct = (
                response.stability_budget_consumed_pct
            )
            center.thaw_remaining_hours = response.thaw_remaining_hours
            center.category_display = response.category_display
            center.decision_reasons = list(response.decision_reasons)

            all_results.append(
                {
                    "file_path": "Multiple sources",
                    "centers_affected": [
                        {
                            "center_name": center.name,
                            "entries_count": len(center.ft2_entries),
                        }
                    ],
                }
            )

    # --- Phase 2: Mapping Boundary ---
    # تحويل RuntimeCenter إلى CenterDTO قبل التقرير
    # هذا يضمن أن طبقة التقرير لا تتعامل مع كائنات المجال أو الكائنات المؤقتة
    center_dtos = []
    for c in centers:
        # 🆕 التحقق من البيانات الأساسية
        if not c.id:
            logger.warning("⚠️ مركز بدون ID - سيتم تخطيه: %s", c)
            continue

        # 🆕 حساب الإحصائيات الحرارية إذا لم تكن موجودة
        stats = getattr(c, "stats", {}) or {}

        if c.ft2_entries and "avg_temp" not in stats:
            temps = []
            for entry in c.ft2_entries:
                # التعامل مع different attribute names
                temp_val = getattr(
                    entry,
                    "temperature",
                    getattr(entry, "value", getattr(entry, "temp", None)),
                )
                if temp_val is not None:
                    try:
                        temps.append(float(temp_val))
                    except (ValueError, TypeError):
                        pass

            if temps:
                stats = {
                    **stats,
                    "avg_temp": sum(temps) / len(temps),
                    "min_temp": min(temps),
                    "max_temp": max(temps),
                }
                logger.debug(
                    "📊 حساب إحصائيات لـ %s: avg=%.2f, min=%.2f, max=%.2f",
                    c.id,
                    stats["avg_temp"],
                    stats["min_temp"],
                    stats["max_temp"],
                )

        # 🆕 إنشاء DTO مع stats في __init__
        dto = CenterDTO(
            id=str(c.id),
            name=str(c.name) if c.name else f"Center-{c.id}",
            device_ids=list(c.device_ids) if c.device_ids else [],
            ft2_entries=list(c.ft2_entries),
            decision=str(c.decision),
            vvm_stage=str(c.vvm_stage),
            alert_level=c.alert_level,
            stability_budget_consumed_pct=float(c.stability_budget_consumed_pct),
            thaw_remaining_hours=c.thaw_remaining_hours,
            category_display=c.category_display,
            decision_reasons=list(c.decision_reasons) if c.decision_reasons else [],
            stats=stats,  # 🆕 تمرير stats هنا مباشرة
        )

        center_dtos.append(dto)
        logger.info(
            "✅ تم تحويل المركز: %s - %s (%d إدخال)",
            dto.id,
            dto.name,
            dto.ft2_entries_count,
        )

    logger.info("📊 إجمالي المراكز المحولة: %d", len(center_dtos))

    # --- Phase 3: Report Generation ---
    # تقرير المراكز
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(center_dtos, centers_report_path)

    # التقارير التفصيلية
    reports_dir = os.path.join(output_dir, "detailed_reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 6. عرض الملخص
    logger.info("%s", "\n" + ("=" * 70))
    logger.info(MessageProvider.get("PIPELINE_SUMMARY_TITLE"))
    logger.info("%s", "=" * 70)
    logger.info(
        MessageProvider.get(
            "FILES_PROCESSED",
            processed_count=len([c for c in center_dtos if c.ft2_entries_count > 0]),
            total_count=len(ft2_files),
        )
    )
    logger.info(MessageProvider.get("FILES_FAILED", failed_count=len(failed_files)))
    logger.info(
        MessageProvider.get("CENTER_REPORT_GENERATED", path=centers_report_path)
    )
    logger.info(
        MessageProvider.get("DETAILED_REPORTS_GENERATED", path=f"{reports_dir}/")
    )

    if failed_files:
        logger.warning(MessageProvider.get("FAILED_FILES_LIST_TITLE"))
        for file, error in failed_files:
            logger.warning("  - %s: %s", file, error)

    logger.info(MessageProvider.get("PIPELINE_COMPLETE", output_dir=output_dir))


def _map_decision_to_vaccine_decision(decision: str) -> VaccineDecision:
    """تحويل القرار النصي إلى VaccineDecision Enum"""
    mapping = {
        "SAFE": VaccineDecision.SAFE,
        "PARTIAL": VaccineDecision.PARTIAL,
        "DISCARD": VaccineDecision.DISCARD,
        "REJECTED": VaccineDecision.DISCARD,
        "REJECTED_HEAT_C": VaccineDecision.DISCARD,
        "REJECTED_EXPIRED": VaccineDecision.DISCARD,
        "WARNING": VaccineDecision.PARTIAL,
        "ACCEPTED": VaccineDecision.SAFE,
    }
    return mapping.get(decision, VaccineDecision.SAFE)


def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description=MessageProvider.get("CLI_DESCRIPTION"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s                           # التشغيل الافتراضي
  %(prog)s --config my_config.yaml   # استخدام تكوين مخصص
  %(prog)s --input ./my_data         # مجلد بيانات مخصص
  %(prog)s --verbose                 # عرض تفاصيل أكثر
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="config/center_profiles.yaml",
        help="مسار ملف تكوين المراكز",
    )
    parser.add_argument(
        "--input", "-i", default="data/input_raw", help="مجلد الملفات الخام المدخلة"
    )
    parser.add_argument(
        "--output", "-o", default="data/output", help="مجلد الملفات المخرجة"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="عرض معلومات تفصيلية"
    )
    parser.add_argument(
        "--generate-data",
        action="store_true",
        dest="generate_data",
        help="إنشاء بيانات اختبار في data/input_raw",
    )

    args = parser.parse_args()

    # ضبط مستوى التسجيل
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")
        # أيضاً تفعيل DEBUG للمكتبات المستخدمة
        logging.getLogger("src.infrastructure.ft2_reader").setLevel(logging.DEBUG)

    try:
        if getattr(args, "generate_data", False):
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()

        run_pipeline(
            config_path=args.config, input_dir=args.input, output_dir=args.output
        )
    except Exception as e:
        logger.error(MessageProvider.get("UNEXPECTED_ERROR", error=e))
        logger.debug("التفاصيل الكاملة للخطأ:")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
