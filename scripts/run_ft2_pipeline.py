#!/usr/bin/env python3
# scripts/run_ft2_pipeline.py
import argparse
import csv
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from scripts.create_test_data import create_test_data
from src.application.dtos.center_dto import CenterDTO
from src.application.mappers.center_mapper import CenterMapper
from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, TemperatureReading)
from src.application.dtos.ft2_entry_dto import FT2EntryDTO
from src.application.use_cases.evaluate_cold_chain_safety_use_case import (
    EvaluateColdChainSafetyUseCase)
from src.domain.services.exposure_analysis_service import ExposureAnalysisService
from src.domain.services.judgment_engine import JudgmentEngine
from src.domain.services.rules_engine import calculate_center_stats
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.adapters.ft2_reader.services.ft2_linker import FT2Linker
from src.infrastructure.logging import get_logger
from src.infrastructure.registry.runtime_center_registry import RuntimeCenterRegistry
from src.infrastructure.utils.yaml_loader import load_yaml
from src.presentation.messages.message_map import MessageProvider
from src.presentation.reporting.csv_reporter import generate_centers_report

# ➕ Phase 1 Imports — Lifecycle + SSOT
from src.application.use_cases.manage_file_lifecycle import ManageFileLifecycleUseCase
from src.application.services.center_impact_service import CenterImpactService
from src.infrastructure.repositories.file_registry_impl import FileRegistryImpl
from src.infrastructure.lifecycle.file_archiver import FileArchiver
from src.infrastructure.security.file_hash import compute_file_hash
from src.infrastructure.ingestion.csv_session_file_reader import CsvSessionFileReader

# ➕ Phase 2 Imports — Fault Isolation + Validation
from src.infrastructure.services.circuit_breaker import FileCircuitBreaker
from src.infrastructure.validators.pydantic_ft2_schema import FT2BatchValidator

# ➕ Phase 3 Imports — Observability
from src.infrastructure.metrics.pipeline_metrics import PipelineRunMetrics

from src.presentation.reporting.professional.professional_vaccine_report import ProfessionalVaccineReport

# ✅ إضافة تخزين Parquet الآمن
from src.infrastructure.storage.parquet_repository import ParquetStorageRepository


def _parse_timestamp(value):
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError(f"Invalid timestamp type: {type(value)}")

    ts = value.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue

    # Fallback to fromisoformat for flexible parsing
    try:
        return datetime.fromisoformat(ts)
    except ValueError as exc:
        raise ValueError(f"Unsupported timestamp format: {value}") from exc



MIN_REPORT_DAYS = 60  # الحد الأدنى للفترة الزمنية للتقرير المخصص


def validate_date_range(
    from_date: Optional[datetime],
    to_date: Optional[datetime],
) -> None:
    """
    يتحقق من صحة نطاق التاريخ:
    - كلا التاريخين يجب أن يكونا موجودَين معاً أو غائبَين معاً.
    - from_date يجب أن يسبق to_date.
    - الفترة لا تقل عن MIN_REPORT_DAYS يوماً (60 يوم).
    يرفع ValueError بوصف واضح عند أي انتهاك.
    """
    if (from_date is None) != (to_date is None):
        raise ValueError(
            "يجب تحديد --from-date و --to-date معاً أو تركهما معاً"
        )
    if from_date is None:
        return  # لا فلترة — وضع افتراضي

    if from_date >= to_date:
        raise ValueError(
            f"--from-date ({from_date.date()}) يجب أن يسبق --to-date ({to_date.date()})"
        )

    delta_days = (to_date - from_date).days
    if delta_days < MIN_REPORT_DAYS:
        raise ValueError(
            f"الفترة الزمنية {delta_days} يوم أقل من الحد الأدنى المسموح ({MIN_REPORT_DAYS} يوم). "
            f"حدد نطاقاً لا يقل عن {MIN_REPORT_DAYS} يوماً."
        )


def filter_entries_by_date(
    entries: List[FT2EntryDTO],
    from_date: Optional[datetime],
    to_date: Optional[datetime],
) -> List[FT2EntryDTO]:
    """
    يُصفّي قراءات FT2 حسب نطاق التاريخ.
    إذا كان النطاق None يُعيد القائمة كاملة بدون تغيير.
    المقارنة تتجاهل timezone (naive vs aware) بأمان.
    """
    if from_date is None or to_date is None:
        return entries

    filtered = []
    for entry in entries:
        ts = _parse_timestamp(entry.timestamp)
        # توحيد naive/aware: إزالة tzinfo للمقارنة الآمنة
        ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
        from_naive = from_date.replace(tzinfo=None) if from_date.tzinfo else from_date
        to_naive = to_date.replace(tzinfo=None) if to_date.tzinfo else to_date
        if from_naive <= ts_naive <= to_naive:
            filtered.append(entry)
    return filtered

logger = get_logger(__name__)


def _system_now() -> datetime:
    return datetime.now()


def setup_directories():
    dirs = ['data/input_raw', 'data/input_ft2', 'data/output', 'data/reports', 'config', 'data/ft2_sessions']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug("تم إنشاء/التحقق من المجلد: %s", d)


def load_centers(config_path: str = "config/center_profiles.yaml") -> List[CenterDTO]:
    try:
        raw = load_yaml(config_path)
        centers_data = raw.get('centers', {})
        centers = []
        for center_id, profile in centers_data.items():
            dto = CenterMapper.from_dict_to_dto(center_id, profile)
            centers.append(dto)
        logger.info("تم تحميل %d مركز تطعيم", len(centers))
        return centers
    except Exception as e:
        logger.critical(MessageProvider.get('CRITICAL_CONFIG_LOAD_FAILED', error=e))
        raise RuntimeError(MessageProvider.get('CONFIG_LOAD_FAILED_STOP')) from e


def extract_device_id_from_file(file_path: Path) -> Optional[str]:
    """استخراج device_id من محتوى ملف FT2 أو من اسم الملف كحل احتياطي."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if 'Serial:' in line or 'device_id:' in line:
                    parts = line.split(':', 1)
                    if len(parts) >= 2:
                        candidate = parts[1].strip()
                        if candidate.isdigit():
                            return candidate
    except Exception as e:
        logger.warning("Could not read device_id from file %s: %s", file_path.name, e)

    stem = file_path.stem
    if '_' in stem:
        candidate = stem.split('_')[0]
        if candidate.isdigit():
            return candidate
        logger.warning(
            "Filename device_id '%s' is not numeric for %s",
            candidate,
            file_path.name,
        )
    else:
        logger.warning(
            "Filename %s does not contain '_' for device_id extraction",
            file_path.name,
        )

    return None


def run_pipeline(
    config_path: str = "config/center_profiles.yaml",
    input_dir: str = "data/input_raw",
    output_dir: str = "data/output",
    force: bool = False,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    run_timestamp: Optional[datetime] = None,
    now_provider: Optional[Callable[[], datetime]] = None,
):
    # ✅ التحقق من صحة نطاق التاريخ قبل أي معالجة
    validate_date_range(from_date, to_date)

    logger.info(MessageProvider.get('PIPELINE_START'))
    if force:
        logger.warning("⚠️ وضع --force مفعّل: سيتم إعادة معالجة جميع الملفات")
    if from_date and to_date:
        delta = (to_date - from_date).days
        logger.info(
            "📅 وضع التقرير المخصص: %s → %s (%d يوم)",
            from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d'), delta
        )

    now = now_provider or _system_now
    run_ts = run_timestamp or now()
    run_id = run_ts.strftime("%Y%m%d_%H%M%S")
    metrics = PipelineRunMetrics(run_id=run_id)

    setup_directories()

    # 1. تحميل المراكز
    centers = load_centers(config_path)

    for center in centers:
        for unit in center.equipment_units:
            if unit.device_id and unit.device_id.startswith('Device_'):
                unit.device_id = unit.device_id.replace('Device_', '')

    center_registry = RuntimeCenterRegistry(centers)
    file_registry = FileRegistryImpl(registry_path=Path("data/registry/processed_files.json"))
    archiver = FileArchiver(base_data_path=Path("data"))
    lifecycle_uc = ManageFileLifecycleUseCase(
        file_registry=file_registry,
        center_registry=center_registry
    )

    # 3. تهيئة المعالجة التزايدية
    from src.infrastructure.registry.session_registry import SessionRegistry
    from src.application.services.incremental_processor import IncrementalPipelineProcessor
    from src.infrastructure.output.centers_report_manager import CentersReportManager

    session_registry = SessionRegistry(Path("data/registry/session_registry.json"))
    parquet_storage = ParquetStorageRepository(Path("data/ft2_sessions"))
    incremental_processor = IncrementalPipelineProcessor(
        session_registry,
        parquet_storage,
        file_reader=CsvSessionFileReader(),
    )
    report_manager = CentersReportManager(Path(os.path.join(output_dir, "centers_report.tsv")))

    # 5. تصنيف الملفات
    logger.info("🔍 تصنيف الملفات قبل المعالجة...")
    input_raw_path = Path(input_dir)
    csv_files = [input_raw_path / f for f in os.listdir(input_dir) if f.endswith(('.csv', '.tsv'))]

    classification = lifecycle_uc.classify_files(csv_files, run_id=run_id, force=force)
    files_to_process = classification.ready_for_processing

    logger.info("📊 نتائج التصنيف: %s", classification.summary_ar())

    # تهيئة متغيرات التتبع
    processed_results: List[dict] = []
    failed_files: List[tuple] = []

    # 6. معالجة تزايدية
    logger.info("🔄 بدء المعالجة التزايدية للبيانات...")

    for csv_path in files_to_process:
        try:
            result = incremental_processor.process_file(csv_path, force=force)

            if result.get("status") == "skipped":
                logger.info(f"⏭️ تم تخطي {csv_path.name} (الفترة معالجة سابقاً)")
                processed_results.append({"file": csv_path.name, "status": "skipped"})
                continue

            logger.info(f"✅ تم دمج بيانات جديدة للجهاز {result['device_id']} | {result.get('new_readings', 0)} قراءة جديدة")

            # تحديث unit.ft2_entries من الجلسة المدمجة
            center = center_registry.get_center_by_device_id(result["device_id"])
            if center:
                for unit in center.equipment_units:
                    if unit.device_id == result["device_id"]:

                        unit.ft2_entries = [
                            FT2EntryDTO(
                                id=str(row.get("id", f"{row.get('device_id', unit.device_id)}_{row['timestamp']}")),
                                timestamp=row["timestamp"],
                                temperature=float(row["temperature"]),
                                device_id=str(row.get("device_id", unit.device_id)),
                                duration_minutes=int(row.get("duration_minutes", 0)),
                                vaccine_type=row.get("vaccine_type"),
                                batch=row.get("batch"),
                            )
                            for row in parquet_storage.read_session(result["device_id"])
                        ]

            processed_results.append({"file": csv_path.name, "status": "processed"})

        except Exception as e:
            logger.error(f"❌ فشل معالجة الملف {csv_path.name}: {e}")
            failed_files.append((csv_path.name, str(e)))
            processed_results.append({"file": csv_path.name, "status": "failed"})

    # 7. تطبيق القواعد وإنشاء التقارير PDF
    logger.info(" Applying rules via EvaluateColdChainSafetyUseCase...")

    # ✅ فلترة البيانات حسب النطاق الزمني المخصص (إذا حُدِّد)
    if from_date and to_date:
        total_before = sum(len(u.ft2_entries) for c in centers for u in c.equipment_units if u.ft2_entries)
        for center in centers:
            for unit in center.equipment_units:
                if unit.ft2_entries:
                    unit.ft2_entries = filter_entries_by_date(unit.ft2_entries, from_date, to_date)
        total_after = sum(len(u.ft2_entries) for c in centers for u in c.equipment_units if u.ft2_entries)
        logger.info(
            "📅 بعد الفلترة الزمنية: %d قراءة من أصل %d (فترة: %s → %s)",
            total_after, total_before,
            from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d'),
        )

    use_case = EvaluateColdChainSafetyUseCase(
        exposure_service=ExposureAnalysisService(),
        judgment_engine=JudgmentEngine(),
    )

    for center in centers:
        for unit in center.equipment_units:
            if not unit.ft2_entries:
                unit.decision = 'NO_DATA_IN_RANGE' if (from_date and to_date) else 'NO_DATA'
                continue

            readings = tuple(
                TemperatureReading(
                    value=float(entry.temperature),
                    timestamp=_parse_timestamp(entry.timestamp),
                    device_id=unit.device_id,
                )
                for entry in unit.ft2_entries
            )

            request = EvaluateColdChainSafetyRequest(
                center_id=center.id,
                center_name=f"{center.name} — {unit.equipment_name}",
                readings=readings,
                temperature_ranges=unit.temperature_ranges,
                decision_thresholds=unit.decision_thresholds,
            )
            response = use_case.execute(request)

            unit.decision = response.decision
            unit.vvm_stage = response.vvm_stage
            unit.alert_level = response.alert_level
            unit.stability_budget_consumed_pct = response.stability_budget_consumed_pct
            unit.thaw_remaining_hours = response.thaw_remaining_hours
            unit.category_display = response.category_display
            unit.decision_reasons = list(response.decision_reasons)
            unit.stats = calculate_center_stats(unit)

            # إنشاء التقرير PDF
            try:
                report_generator = ProfessionalVaccineReport()

                report_context = {
                    "center_name": f"{center.name} — {unit.equipment_name}",
                    "center_id": center.id,
                    "device_id": unit.device_id,
                    "equipment_type": unit.equipment_name,
                    "vaccine_type": getattr(unit, 'vaccine_type', 'غير محدد'),
                    "decision": unit.decision,
                    "vvm_stage": getattr(unit, 'vvm_stage', 'NONE'),
                    "alert_level": getattr(unit, 'alert_level', None),
                    "stability_budget_consumed_pct": getattr(unit, 'stability_budget_consumed_pct', 0.0),
                    "temp_min": unit.stats.get("temp_min", "—") if hasattr(unit, 'stats') else "—",
                    "temp_max": unit.stats.get("temp_max", "—") if hasattr(unit, 'stats') else "—",
                    "exposure_minutes": unit.stats.get("exposure_minutes", 0) if hasattr(unit, 'stats') else 0,
                    "category_display": getattr(unit, 'category_display', ''),
                    "decision_reasons": " | ".join(getattr(unit, 'decision_reasons', [])),
                    "supervisor_name": getattr(center, 'supervisor_name', 'مشرف التطعيم'),
                    "report_id": f"FT2-{center.id}-{run_ts.strftime('%Y%m%d%H%M%S')}",
                    "language": getattr(center, 'language', 'ar'),
                    "date_range_from": from_date.strftime('%Y-%m-%d') if from_date else None,
                    "date_range_to": to_date.strftime('%Y-%m-%d') if to_date else None,
                    "date_range_days": (to_date - from_date).days if (from_date and to_date) else None,
                }

                filename = f"{center.id}_{unit.equipment_name.replace(' ', '_')}_vaccine_report.pdf"

                pdf_path = report_generator.generate_vaccine_a4(
                    context=report_context,
                    readings=unit.ft2_entries,
                    filename=filename,
                )

                logger.info(f"📄 تم إنشاء تقرير PDF للمركز: {center.name} — {unit.equipment_name}")
                logger.info(f"   → {pdf_path}")

            except Exception as report_err:
                logger.error(f"❌ فشل إنشاء تقرير PDF للمركز {center.name}: {report_err}")

    # 8. إنشاء تقرير المراكز + الملخص
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(centers, centers_report_path)

    logger.info("🏁 اكتمل خط المعالجة التزايدية بنجاح")
    logger.info(MessageProvider.get('PIPELINE_COMPLETE', output_dir=output_dir))

    # ===========================================
    # تسجيل الملفات المعالجة في Registry
    # ===========================================
    if processed_results:
        for path in files_to_process:
            if path.exists():
                try:
                    file_hash = compute_file_hash(path)
                    device_id = extract_device_id_from_file(path)
                    if not device_id:
                        logger.error(
                            "فشل استخراج device_id للملف %s، تم تجاهل التسجيل",
                            path.name,
                        )
                        continue

                    file_registry.mark_processed(
                        file_hash=file_hash,
                        device_id=device_id,
                        run_id=run_id,
                        processed_at=run_ts
                    )
                except Exception as e:
                    logger.warning("فشل تسجيل الملف: %s - %s", path.name, str(e))

        logger.info("✅ سُجّل %d ملف في registry", len(files_to_process))

    # حفظ قائمة الملفات المتجاهلة
    reports_dir = os.path.join(output_dir, "detailed_reports")
    os.makedirs(reports_dir, exist_ok=True)

    ignored = [r for r in processed_results if r.get('status') == 'ignored']
    if ignored:
        ignored_path = os.path.join(output_dir, "ignored_files.tsv")
        with open(ignored_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["file", "status", "reason"])
            for r in ignored:
                writer.writerow([r['file'], r['status'], r.get('reason', '')])
        logger.info("تم حفظ قائمة الملفات المتجاهلة: %s", ignored_path)

    # عرض الملخص
    total = len(csv_files)
    processed_cnt = sum(1 for r in processed_results if r.get('status') == 'processed')
    ignored_cnt = len(ignored)
    failed_cnt = len(failed_files)

    logger.info("\n" + "=" * 70)
    logger.info(MessageProvider.get('PIPELINE_SUMMARY_TITLE'))
    logger.info("=" * 70)
    logger.info(MessageProvider.get('FILES_PROCESSED', processed_count=processed_cnt, total_count=total))
    logger.info("الملفات المعالجة بنجاح: %d", processed_cnt)
    logger.info("الملفات المتجاهلة: %d", ignored_cnt)
    for r in ignored:
        logger.info("  - %s : %s", r['file'], r.get('reason', ''))
    logger.info("الملفات الفاشلة: %d", failed_cnt)
    if failed_cnt:
        logger.warning(MessageProvider.get('FAILED_FILES_LIST_TITLE'))
        for file, err in failed_files:
            logger.warning("  - %s: %s", file, err)

    logger.info("مراكز محمّلة: %d", len(centers))

    affected_count = CenterImpactService.count_affected_centers(centers)
    yaml_count = center_registry.get_registered_center_count()

    # ✅ فحص SSOT مشروط — لا معنى له إذا لم تُعالَج ملفات جديدة
    if files_to_process:
        is_valid, ssot_message = CenterImpactService.verify_ssot(yaml_count, affected_count)
        logger.info("🎯 %s", ssot_message)
    else:
        is_valid = True
        logger.info(
            "🎯 SSOT: ⏭️ تخطي — لا ملفات جديدة في هذا التشغيل "
            "(YAML: %d مركز | استخدم --force لإعادة المعالجة)",
            yaml_count,
        )

    metrics.affected_centers_count = affected_count
    metrics.finished_at = now()

    # Phase 3: Print final metrics summary
    metrics.print_bilingual_summary(logger)

    logger.info("مراكز متأثرة (ببيانات): %d", affected_count)
    logger.info(MessageProvider.get('CENTER_REPORT_GENERATED', path=centers_report_path))
    logger.info(MessageProvider.get('DETAILED_REPORTS_GENERATED', path=f"{reports_dir}/"))
    logger.info(MessageProvider.get('PIPELINE_COMPLETE', output_dir=output_dir))


def main():
    parser = argparse.ArgumentParser(description=MessageProvider.get('CLI_DESCRIPTION'))
    parser.add_argument('--config', '-c', default='config/center_profiles.yaml')
    parser.add_argument('--input', '-i', default='data/input_raw')
    parser.add_argument('--output', '-o', default='data/output')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--generate-data', action='store_true', dest='generate_data')
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='إعادة معالجة الملفات المسجلة مسبقاً (يتجاهل Registry)',
    )
    parser.add_argument(
        '--from-date',
        dest='from_date',
        default=None,
        metavar='YYYY-MM-DD',
        help='تاريخ بداية التقرير المخصص (مثال: 2024-01-01)',
    )
    parser.add_argument(
        '--to-date',
        dest='to_date',
        default=None,
        metavar='YYYY-MM-DD',
        help='تاريخ نهاية التقرير المخصص (مثال: 2024-06-30) — الفترة لا تقل عن 60 يوماً',
    )

    args = parser.parse_args()

    # ✅ تحويل التواريخ من نص إلى datetime
    def _parse_cli_date(value: str, arg_name: str) -> datetime:
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d')
        except ValueError:
            parser.error(f"{arg_name} يجب أن يكون بصيغة YYYY-MM-DD (مثال: 2024-01-01)")

    from_date = _parse_cli_date(args.from_date, '--from-date') if args.from_date else None
    to_date   = _parse_cli_date(args.to_date,   '--to-date')   if args.to_date   else None

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")

    try:
        if args.generate_data:
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()
        # ✅ تمرير force إلى run_pipeline
        run_pipeline(
            config_path=args.config,
            input_dir=args.input,
            output_dir=args.output,
            force=args.force,
            from_date=from_date,
            to_date=to_date,
        )
    except Exception as e:
        logger.exception("❌ خطأ غير متوقع أثناء run_pipeline")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
