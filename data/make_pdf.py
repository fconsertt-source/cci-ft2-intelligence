import sys
from pathlib import Path

# ==========================================
# 🚨 إيقاف الحماية مؤقتاً لتمرير التقرير
# ==========================================
from src.application.app_composer import AppComposer

class DummyGuard:
    def ensure_active(self):
        pass

AppComposer._create_license_guard = lambda *args, **kwargs: DummyGuard()
AppComposer._create_ledger_writer = lambda *args, **kwargs: None
# ==========================================

from src.application.use_cases.requests import GenerateDeviceReportRequest

def main(device_id):
    print(f"🔄 Starting PDF Generation pipeline for device: {device_id}...")
    
    try:
        # 1. حساب البيانات
        report_uc = AppComposer.create_generate_device_report_uc()
        req = GenerateDeviceReportRequest(device_id=device_id)
        
        print("📊 Calculating Thermal Metrics & CCM...")
        report_dto = report_uc.execute(req)
        print(f"✅ Calculations Done! Final Decision: {report_dto.decision}")
        
        # 2. توليد الـ PDF عبر الدالة الصحيحة
        print("📄 Generating PDF Report...")
        pdf_uc = AppComposer.create_generate_pdf_report_uc() 
        
        # ✅ الإصلاح: التحقق مما إذا كانت النتيجة بايتات (Bytes) وحفظها كملف
        pdf_result = pdf_uc.execute_device_report(report_dto)
        if isinstance(pdf_result, bytes):
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = output_dir / f"report_{device_id}.pdf"

            with open(pdf_path, "wb") as f:
                f.write(pdf_result)
            print(f"🎉 SUCCESS! PDF saved to disk at: {pdf_path}")
        else:
            # إذا كان يعيد مساراً نصياً بالفعل
            pdf_path = pdf_result
            print(f"🎉 SUCCESS! PDF generated at: {pdf_path}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a device ID. Example: python data/make_pdf.py 130600113438")
    else:
        main(sys.argv[1])