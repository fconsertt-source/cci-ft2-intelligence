# src/domain/evidence/pdf_extraction_result.py
"""نتيجة استخراج البيانات الأساسية من تقرير PDF"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime  # ← الإصلاح: إضافة datetime هنا

@dataclass(frozen=True)
class PDFExtractionResult:
    """نتيجة استخراج البيانات الأساسية من تقرير PDF"""
    
    # 🔑 البيانات السيادية
    device_id: str
    serial: str
    
    # 📅 نطاق التقرير
    start_date: datetime
    stop_date: datetime
    
    # 🌡️ القيم الحرارية
    min_temperature: Decimal
    max_temperature: Decimal
    avg_temperature: Decimal
    
    # ⚠️ التنبيهات
    alarm_count: int
    
    # 📊 إحصائيات
    total_readings: int
    
    # 🏷️ معلومات النظام
    extraction_timestamp: datetime  # ← الآن معرّف بشكل صحيح
    pdf_hash: str  # SHA256 للملف الأصلي