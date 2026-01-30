import os
import sys
from pathlib import Path

# إضافة المسار
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.logging import get_logger
from src.application.mappers.center_mapper import to_center_dto
from src.application.dtos.center_dto import CenterDTO

logger = get_logger(__name__)


class CenterEntity:
    """Lightweight internal entity used during pipeline processing only."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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

    # Map the TSV to internal Entities and then to DTOs for presentation
    centers = []
    for line in fake_report.splitlines():
        if line.startswith('center_id'):
            continue
        parts = line.split('\t')
        if len(parts) < 13:
            continue
        ent = CenterEntity(
            id=parts[0],
            name=parts[1],
            decision=parts[2],
            vvm_stage=parts[3],
            recommended_action=parts[4],
            num_ft2_entries=int(parts[5]),
            has_freeze=parts[6],
            has_ccm_violation=parts[7],
            freeze_duration_mins=int(parts[8]),
            heat_duration_mins=int(parts[9]),
            avg_temperature=float(parts[10]),
            min_temperature=float(parts[11]),
            max_temperature=float(parts[12]),
            decision_reasons=[parts[4]]
        )
        centers.append(ent)

    dtos = [to_center_dto(c) for c in centers]
    logger.info("Mapped %d internal centers to DTOs for presentation", len(dtos))
    
    # 3. إنشاء PDF
    logger.info("📄 الخطوة 3: إنشاء تقرير PDF...")

    try:
        from src.reporting.simple_pdf_generator import create_simple_pdf
        pdf_path = create_simple_pdf()
        if pdf_path:
            logger.info("✅ تم إنشاء التقرير PDF: %s", pdf_path)
            return True
    except Exception as e:
        logger.warning("⚠️  لم يتم إنشاء PDF: %s", e)
        logger.info("📋 لكن التقرير النصي جاهز في: data/output/centers_report.tsv")
        return True
    
    return False

if __name__ == "__main__":
    success = run_simple_pipeline()
    if success:
        logger.info("🎉 اكتمل التشغيل المبسط بنجاح!")
    else:
        logger.error("❌ فشل التشغيل المبسط")
