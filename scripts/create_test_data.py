import os
import sys
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# allow importing src
sys.path.append(str(Path(__file__).parent.parent))
from src.infrastructure.logging import get_logger
logger = get_logger(__name__)

def create_test_data():
    """إنشاء بيانات اختبار لخط المعالجة"""
    output_dir = "data/input_raw"
    os.makedirs(output_dir, exist_ok=True)
    
    # سيناريوهات الاختبار بناءً على center_profiles.yaml
    scenarios = [
        {
            "device_id": "130600112764", # Hospital - Safe (ضمن النطاق 2-8)
            "base_temp": 5.0,
            "variance": 1.0,
            "name": "safe_hospital"
        },
        {
            "device_id": "130600112767", # Clinic - Freeze (تجميد)
            "base_temp": -2.0,
            "variance": 0.5,
            "name": "freeze_clinic"
        },
        {
            "device_id": "130600112769", # Mobile - Heat (CCM Violation)
            "base_temp": 12.0,
            "variance": 2.0,
            "name": "heat_mobile"
        }
    ]
    
    logger.info("🚀 جاري إنشاء ملفات اختبار في %s...", output_dir)
    
    for scenario in scenarios:
        filename = f"{scenario['name']}_{scenario['device_id']}.csv"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # كتابة الرأس المتوافق مع FT2Parser
            writer.writerow(['device_id', 'timestamp', 'temperature', 'vaccine_type', 'batch'])
            
            # توليد بيانات لمدة 24 ساعة (قراءة كل 15 دقيقة)
            base_time = datetime.now() - timedelta(days=1)
            records = 96 # 24 ساعة * 4 قراءات/ساعة
            
            for i in range(records):
                current_time = base_time + timedelta(minutes=15*i)
                
                # محاكاة درجة الحرارة
                temp = scenario['base_temp'] + random.uniform(-scenario['variance'], scenario['variance'])
                
                writer.writerow([
                    scenario['device_id'],
                    current_time.isoformat(),
                    f"{temp:.2f}",
                    "COVID-19",
                    "BATCH-2024-001"
                ])
        
        logger.info("✅ تم إنشاء: %s", filename)

if __name__ == "__main__":
    create_test_data()