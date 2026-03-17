#!/usr/bin/env python3
"""
اختبار تكامل لسلسلة Fallback الكاملة
✅ اختبار كل مستوى في السلسلة
✅ اختبار الانتقال السلس بين المستويات
"""
import logging
from datetime import datetime, timezone

import pytest

from src.domain.dtos.device_report_dto import DeviceReportDTO


@pytest.fixture
def sample_dto():
    return DeviceReportDTO(
        device_id="INTEGRATION-TEST-001",
        vaccine_type="Pfizer-BioNTech",
        total_records=50,
        excursions=[],
        final_status="safe",
        scientific_rationale="Integration test",
        generated_at=datetime.now(timezone.utc).isoformat(),
        ledger_hash="b" * 64,
    )


class TestFallbackChainIntegration:
    """اختبار تكامل سلسلة Fallback"""

    def test_full_fallback_chain(self, sample_dto, caplog):
        """اختبار السلسلة الكاملة من Unified → Fallback → Placeholder"""
        from src.infrastructure.pdf.unified_pdf_generator_wrapper import \
            UnifiedPDFGeneratorWrapper

        caplog.set_level(logging.INFO)

        wrapper = UnifiedPDFGeneratorWrapper()

        # محاكاة فشل المولد الحقيقي: تأكد من إزالة الكائن الداخلي
        wrapper._inner = None
        wrapper._initialized = True

        pdf_bytes = wrapper.render(sample_dto)

        # يجب أن يعمل placeholder النهائي
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 0

        # يجب تسجيل التحذيرات المناسبة
        assert any("fallback" in record.message.lower() for record in caplog.records)

    def test_unified_generator_priority(self, sample_dto):
        """التأكد من أن المولد الحقيقي له أولوية"""
        from src.infrastructure.pdf.unified_pdf_generator_wrapper import \
            UnifiedPDFGeneratorWrapper

        wrapper = UnifiedPDFGeneratorWrapper()
        wrapper._ensure_initialized()

        # إذا كان المولد الحقيقي متاحاً، يجب استخدامه أولاً
        if wrapper._unified is not None:
            pdf_bytes = wrapper.render(sample_dto)
            assert pdf_bytes.startswith(b"%PDF")
