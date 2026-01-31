import os
import sys
from pathlib import Path

# إضافة المسار
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.logging import get_logger
from src.shared.di_container import create_evaluate_cold_chain_uc
from src.application.dtos.center_dto import CenterDTO
from src.core.services.rules_engine import apply_rules
from src.reporting.csv_reporter import generate_centers_report

logger = get_logger(__name__)


def run_simple_pipeline():
    logger.info("🚀 بدء التشغيل المبسط...")

    # 1. إنشاء بيانات اختبار
    logger.info("🧪 الخطوة 1: إنشاء بيانات اختبار...")
    
    test_data = '''device_id,timestamp,temperature,vaccine_type,batch
130600112764,2024-01-15T08:00:00,5.2,COVID-19,BATCH-2024-001
130600112764,2024-01-15T12:00:00,4.8,COVID-19,BATCH-2024-001
130600112767,2024-01-15T08:00:00,-1.5,COVID-19,BATCH-2024-002
130600112767,2024-01-15T12:00:00,-2.1,COVID-19,BATCH-2024-002
130600112769,2024-01-15T08:00:00,12.5,COVID-19,BATCH-2024-003
130600112769,2024-01-15T12:00:00,14.2,COVID-19,BATCH-2024-003'''
    
    os.makedirs("data/input_raw", exist_ok=True)
    
    with open("data/input_raw/test_data.csv", "w", encoding="utf-8") as f:
        f.write(test_data)

    logger.info("✅ تم إنشاء بيانات الاختبار")
    
    # 2. محاكاة معالجة البيانات
    logger.info("🔄 الخطوة 2: محاكاة معالجة البيانات...")
    
    # إنشاء تقرير وهمي
    os.makedirs("data/output", exist_ok=True)
    
    fake_report = '''center_id\tcenter_name\tdecision\tvvm_stage\trecommended_action\tnum_ft2_entries\thas_freeze\thas_ccm_violation\tfreeze_duration_mins\theat_duration_mins\tavg_temperature\tmin_temperature\tmax_temperature
HOSPITAL_01\tمستشفى المركز الرئيسي\tACCEPTED\tNONE\tاللقاحات سليمة (النوافذ بيضاء). تستخدم بشكل طبيعي\t24\tNO\tNO\t0\t0\t5.0\t4.8\t5.2
CLINIC_02\tعيادة الحي الشمالي\tREJECTED_FREEZE_SENSITIVE\tNONE\tتحقق من خاصية اللقاح: إتلاف الحساسة للتجميد فقط. الباقي سليم\t24\tYES\tNO\t120\t0\t-1.8\t-2.1\t-1.5
MOBILE_03\tوحدة التطعيم المتنقلة\tWARNING_HEAT_A\tA\tاستخدم شلل الأطفال خلال 3 أشهر. باقي اللقاحات طبيعي (المرحلة A)\t24\tNO\tYES\t0\t180\t13.4\t12.5\t14.2'''
    
    with open("data/output/centers_report.tsv", "w", encoding="utf-8") as f:
        f.write(fake_report)

    logger.info("✅ تم إنشاء التقرير الوهمي")

    # Map the TSV directly into CenterDTOs (NO Entities leave the Domain)
    centers_dto = []
    for line in fake_report.splitlines():
        if line.startswith('center_id'):
            continue
        parts = line.split('\t')
        if len(parts) < 13:
            continue

        # create lightweight ft2 entry objects expected by RulesEngine
        # here we create an example list (empty durations) to satisfy report logic
        ft2_entries = []

        dto = CenterDTO(
            id=parts[0],
            name=parts[1],
            device_ids=[],
            ft2_entries=ft2_entries,
            decision=parts[2],
            vvm_stage=parts[3],
            alert_level=None,
            stability_budget_consumed_pct=0.0,
            thaw_remaining_hours=None,
            category_display=None,
            decision_reasons=[parts[4]]
        )
        centers_dto.append(dto)

    logger.info("Mapped %d rows to CenterDTOs (no Entities passed outside Domain)", len(centers_dto))

    # Demonstrate use of the Composition Root (di_container) — create UC (reader=None for demo)
    uc = create_evaluate_cold_chain_uc(reader=None)
    logger.debug("Created EvaluateColdChainSafetyUC via di_container: %s", type(uc).__name__)

    # Apply rules (analysis) on each DTO (RulesEngine accepts DTO-like objects)
    for center in centers_dto:
        # apply_rules will set `decision` and `decision_reasons` on the DTO
        apply_rules(center)

    # Pass DTOs only to the reporting layer
    centers_report_path = "data/output/centers_report.tsv"
    os.makedirs(os.path.dirname(centers_report_path), exist_ok=True)
    generate_centers_report(centers_dto, centers_report_path)

    logger.info("✅ تم إنشاء التقرير عبر generate_centers_report: %s", centers_report_path)
    return True

if __name__ == "__main__":
    success = run_simple_pipeline()
    if success:
        logger.info("🎉 اكتمل التشغيل المبسط بنجاح!")
    else:
        logger.error("❌ فشل التشغيل المبسط")
