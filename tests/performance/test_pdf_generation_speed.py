# tests/performance/test_pdf_generation_speed.py
#!/usr/bin/env python3
"""Performance benchmark that measures time, size, and memory footprint for PDF generation."""
import time
import tracemalloc
from datetime import datetime

import pytest

# ✅ استيراد من المسار الصحيح
from src.domain.dtos.device_report_dto import DeviceReportDTO, ReportStatus


def create_realistic_dto() -> DeviceReportDTO:
    """إنشاء DTO واقعي مع قراءات متعددة"""
    readings = []
    base_time = datetime.now()
    for i in range(100):  # 100 قراءة
        readings.append(
            {
                "timestamp": base_time.replace(minute=i % 60),
                "temperature": 4.0 + (i % 5) * 0.5,
                "device_id": "TEST-REALISTIC",
            }
        )

    return DeviceReportDTO(
        device_id="TEST-REALISTIC",
        vaccine_type="Pfizer-BioNTech",
        total_records=len(readings),
        excursions=(),
        final_status="safe",
        scientific_rationale="Test rationale",
        generated_at=datetime.now(),
    )


@pytest.mark.performance
def test_pdf_generation_performance():
    """اختبار الزمن + الحجم + الذاكرة معاً"""
    try:
        from src.infrastructure.pdf.unified_pdf_generator import UnifiedPDFGenerator
    except ImportError:
        pytest.skip("UnifiedPDFGenerator not available yet")

    try:
        generator = UnifiedPDFGenerator()
    except RuntimeError as e:
        # missing reportlab typically raises here
        pytest.skip(f"UnifiedPDFGenerator cannot be constructed: {e}")
    dto = create_realistic_dto()

    # ✅ تتبع الذاكرة
    tracemalloc.start()

    start = time.perf_counter()
    pdf_bytes = generator.render(dto)
    elapsed = time.perf_counter() - start

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # ✅ قيود الزمن
    TEMPORARY_THRESHOLD = 20.0  # ثانية (أسبوع 2)
    FINAL_THRESHOLD = 10.0  # ثانية (أسبوع 8)
    assert elapsed < TEMPORARY_THRESHOLD, f"PDF generation too slow: {elapsed}s"

    # ✅ قيود الحجم
    MAX_REASONABLE_SIZE_MB = 5
    size_mb = len(pdf_bytes) / (1024 * 1024)
    assert size_mb < MAX_REASONABLE_SIZE_MB, f"PDF too large: {size_mb:.2f}MB"

    # ✅ قيود الذاكرة - جديد!
    MAX_PEAK_MEMORY_MB = 300
    peak_mb = peak / (1024 * 1024)
    assert peak_mb < MAX_PEAK_MEMORY_MB, f"Peak memory too high: {peak_mb:.2f}MB"

    # 📊 Log للأداء للتتبع الأسبوعي
    print("\n=== PDF Performance ===")
    print(f"Time: {elapsed:.2f}s (threshold: {FINAL_THRESHOLD}s)")
    print(f"Size: {size_mb:.2f}MB (limit: {MAX_REASONABLE_SIZE_MB}MB)")
    print(f"Peak Memory: {peak_mb:.2f}MB (limit: {MAX_PEAK_MEMORY_MB}MB)")
    print("========================\n")
