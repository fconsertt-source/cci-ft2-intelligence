#!/usr/bin/env python3
# scripts/run_ft2_pipeline.py
import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from scripts.create_test_data import create_test_data
from src.application.dtos.center_dto import CenterDTO
from src.application.mappers.center_mapper import CenterMapper
from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, TemperatureReading)
from src.application.use_cases.evaluate_cold_chain_safety_use_case import (
    EvaluateColdChainSafetyUseCase)
from src.domain.services.rules_engine import calculate_center_stats
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.adapters.ft2_reader.services.ft2_linker import FT2Linker
from src.infrastructure.logging import get_logger
from src.infrastructure.utils.yaml_loader import load_yaml
from src.presentation.messages.message_map import MessageProvider
from src.presentation.reporting.csv_reporter import generate_centers_report

logger = get_logger(__name__)


def setup_directories():
    dirs = ['data/input_raw', 'data/input_ft2', 'data/output', 'data/reports', 'config']
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


def run_pipeline(
    config_path: str = "config/center_profiles.yaml",
    input_dir: str = "data/input_raw",
    output_dir: str = "data/output",
):
    logger.info(MessageProvider.get('PIPELINE_START'))
    setup_directories()

    # 1. تحميل المراكز (CenterDTO مع equipment_units)
    centers = load_centers(config_path)

    # 2. بناء خريطة device_id -> EquipmentDTO
    device_map = {}
    for center in centers:
        for unit in center.equipment_units:
            if unit.device_id:
                device_map[unit.device_id] = unit

    # 3. جمع ملفات CSV/TSV
    ft2_files = []
    if os.path.exists(input_dir):
        ft2_files = [f for f in os.listdir(input_dir) if f.endswith(('.csv', '.tsv'))]

    if not ft2_files:
        logger.warning(MessageProvider.get('NO_FILES_TO_PROCESS', path=input_dir))
        if not os.listdir(input_dir):
            logger.info(MessageProvider.get('EMPTY_INPUT_DIR_HINT'))
        return

    logger.info(MessageProvider.get('FILES_FOUND_TO_PROCESS', count=len(ft2_files), path=input_dir))

    failed_files = []
    processed_results = []

    # 4. معالجة كل ملف
    for ft2_file in ft2_files:
        ft2_path = os.path.join(input_dir, ft2_file)
        try:
            entries = FT2Parser.parse_file(ft2_path)
            FT2Linker.link(entries, centers)  # يربط الإدخالات بـ equipment_units عبر device_map

            # تحديد ما إذا كان الملف مرتبطاً بأي جهاز
            device_ids_in_file = {getattr(e, 'device_id', None) for e in entries if hasattr(e, 'device_id')}
            linked = any(d in device_map for d in device_ids_in_file)

            if not linked:
                logger.debug("تجاهل الملف %s: لا يوجد تطابق مع أي جهاز", ft2_file)
                processed_results.append({'file': ft2_file, 'status': 'ignored', 'reason': 'no_matching_device'})
            else:
                logger.info("✅ تمت معالجة وربط: %s", ft2_file)
                processed_results.append({'file': ft2_file, 'status': 'processed'})
        except Exception as e:
            logger.error(MessageProvider.get('FILE_PROCESSING_FAILED', file=ft2_file, error=e))
            failed_files.append((ft2_file, str(e)))
            processed_results.append({'file': ft2_file, 'status': 'failed', 'reason': str(e)})

    # 5. تطبيق القواعد على كل وحدة (EquipmentDTO)
    logger.info(" Applying rules via EvaluateColdChainSafetyUseCase...")
    use_case = EvaluateColdChainSafetyUseCase()

    for center in centers:
        for unit in center.equipment_units:
            if not unit.ft2_entries:
                unit.decision = 'NO_DATA'
                continue

            readings = tuple(
                TemperatureReading(
                    value=entry.temperature,
                    timestamp=entry.timestamp,
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

    # 6. إنشاء التقرير (centers هي CenterDTO مع equipment_units)
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(centers, centers_report_path)

    # 7. حفظ قائمة الملفات المتجاهلة
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

    # 8. عرض الملخص
    total = len(ft2_files)
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
    active = sum(1 for c in centers for u in c.equipment_units if u.ft2_entries)
    logger.info("مراكز متأثرة (ببيانات): %d", active)
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

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")

    try:
        if args.generate_data:
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()
        run_pipeline(config_path=args.config, input_dir=args.input, output_dir=args.output)
    except Exception as e:
        logger.error(MessageProvider.get('UNEXPECTED_ERROR', error=e))
        sys.exit(1)


if __name__ == "__main__":
    main()