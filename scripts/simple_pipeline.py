import os
import sys
from pathlib import Path

# إضافة المسار
sys.path.append(str(Path(__file__).parent.parent))

def run_simple_pipeline():
    print("🚀 بدء التشغيل المبسط...")
    
    # 1. إنشاء بيانات اختبار
    print("🧪 الخطوة 1: إنشاء بيانات اختبار...")
    
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
    
    print("✅ تم إنشاء بيانات الاختبار")
    
    # 2. محاكاة معالجة البيانات
    print("🔄 الخطوة 2: محاكاة معالجة البيانات...")
    
    # إنشاء تقرير وهمي
    os.makedirs("data/output", exist_ok=True)
    
    fake_report = '''center_id\tcenter_name\tdecision\tvvm_stage\trecommended_action\tnum_ft2_entries\thas_freeze\thas_ccm_violation\tfreeze_duration_mins\theat_duration_mins\tavg_temperature\tmin_temperature\tmax_temperature
HOSPITAL_01\tمستشفى المركز الرئيسي\tACCEPTED\tNONE\tاللقاحات سليمة (النوافذ بيضاء). تستخدم بشكل طبيعي\t24\tNO\tNO\t0\t0\t5.0\t4.8\t5.2
CLINIC_02\tعيادة الحي الشمالي\tREJECTED_FREEZE_SENSITIVE\tNONE\tتحقق من خاصية اللقاح: إتلاف الحساسة للتجميد فقط. الباقي سليم\t24\tYES\tNO\t120\t0\t-1.8\t-2.1\t-1.5
MOBILE_03\tوحدة التطعيم المتنقلة\tWARNING_HEAT_A\tA\tاستخدم شلل الأطفال خلال 3 أشهر. باقي اللقاحات طبيعي (المرحلة A)\t24\tNO\tYES\t0\t180\t13.4\t12.5\t14.2'''
    
    with open("data/output/centers_report.tsv", "w", encoding="utf-8") as f:
        f.write(fake_report)
    
    print("✅ تم إنشاء التقرير الوهمي")
    
    # 3. إنشاء PDF
    print("📄 الخطوة 3: إنشاء تقرير PDF...")
    
    try:
        from src.reporting.simple_pdf_generator import create_simple_pdf
        pdf_path = create_simple_pdf()
        if pdf_path:
            print(f"✅ تم إنشاء التقرير PDF: {pdf_path}")
            return True
    except Exception as e:
        print(f"⚠️  لم يتم إنشاء PDF: {e}")
        print("📋 لكن التقرير النصي جاهز في: data/output/centers_report.tsv")
        return True
    
    return False

if __name__ == "__main__":
    success = run_simple_pipeline()
    if success:
        print("🎉 اكتمل التشغيل المبسط بنجاح!")
    else:
        print("❌ فشل التشغيل المبسط")
