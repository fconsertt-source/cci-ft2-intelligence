# tests/unit/test_pdf_structural_extractor.py
from decimal import Decimal
from pathlib import Path

import pytest

from src.infrastructure.security.pdf_structural_extractor import \
    PDFStructuralExtractor

# تحديد مسارات الملفات
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "ft2"
PDF_DIR = FIXTURES_DIR / "pdf"
TXT_DIR = FIXTURES_DIR / "txt"


class TestPDFStructuralExtractor:

    def test_pattern_extraction_without_pdf(self):
        """
        اختبار استخراج الأنماط بدون ملف PDF فعلي
        يستخدم نصاً محاكياً يمثل محتوى تقرير Berlinger
        """
        extractor = PDFStructuralExtractor()

        # نص محاكي لتقرير Berlinger PDF
        mock_pdf_text = """
Berlinger Q-tag Fridge-tag 2 E Report
Device: Q-tag Fridge-tag 2 E
Serial: 130600112748
Fw Vers: 3.4p0o

Report history length: 60

Temperature Summary:
Min T: +1.8
Max T: +6.8
Avrg T: +3.5

Alarm Count:
t Acc: 0
t Acc: 0
        """.strip()

        # اختبار استخراج Serial
        serial = extractor._extract_serial(mock_pdf_text)
        assert (
            serial == "130600112748"
        ), f"الـ Serial المتوقع: 130600112748، المستخرج: {serial}"

        # اختبار استخراج درجات الحرارة
        min_temp = extractor._extract_min_temperature(mock_pdf_text)
        assert min_temp == Decimal(
            "1.8"
        ), f"أقل حرارة متوقعة: 1.8، المستخرجة: {min_temp}"

        max_temp = extractor._extract_max_temperature(mock_pdf_text)
        assert max_temp == Decimal(
            "6.8"
        ), f"أعلى حرارة متوقعة: 6.8، المستخرجة: {max_temp}"

        avg_temp = extractor._extract_avg_temperature(mock_pdf_text)
        assert avg_temp == Decimal("3.5"), f"المتوسط المتوقع: 3.5، المستخرج: {avg_temp}"

        # اختبار استخراج عدد القراءات
        readings = extractor._extract_total_readings(mock_pdf_text)
        assert readings == 60, f"عدد القراءات المتوقع: 60، المستخرج: {readings}"

        print("✓ جميع اختبارات الأنماط نجحت")

    def test_alarm_count_extraction(self):
        """اختبار استخراج عدد التنبيهات"""
        extractor = PDFStructuralExtractor()

        # حالة مع تنبيهات
        text_with_alarms = "t Acc: 5\nt Acc: 3\nt Acc: 0"
        count = extractor._extract_alarm_count(text_with_alarms)
        assert count == 8, f"إجمالي التنبيهات المتوقع: 8، المستخرج: {count}"

        # حالة بدون تنبيهات
        text_no_alarms = "t Acc: 0\nt Acc: 0\nt Acc: 0"
        count = extractor._extract_alarm_count(text_no_alarms)
        assert count == 0, f"إجمالي التنبيهات المتوقع: 0، المستخرج: {count}"

        print("✓ اختبار التنبيهات نجح")

    @pytest.mark.skipif(
        not (PDF_DIR / "130600112748_report.pdf").exists(),
        reason="ملف الاختبار غير موجود",
    )
    def test_extract_valid_pdf(self):
        """اختبار استخراج البيانات من ملف PDF صالح (إذا وجد)"""
        pdf_path = PDF_DIR / "130600112748_report.pdf"
        extractor = PDFStructuralExtractor()

        result = extractor.extract(pdf_path)

        assert result.device_id == "Q-tag Fridge-tag 2 E"
        assert result.serial == "130600112748"
        assert result.min_temperature >= Decimal("1.0")
        assert result.max_temperature <= Decimal("10.0")
        assert result.alarm_count >= 0
        assert len(result.pdf_hash) == 64  # SHA256

    @pytest.mark.skipif(
        not (PDF_DIR / "130600112748_report.pdf").exists(),
        reason="ملفات الاختبار غير مكتملة",
    )
    def test_extract_with_corresponding_txt(self):
        """اختبار استخراج PDF ومقارنته مع ملف TXT المقابل (إذا وجد)"""
        pdf_path = PDF_DIR / "130600112748_report.pdf"
        txt_path = TXT_DIR / "130600112748_202507070910.txt"

        if not txt_path.exists():
            pytest.skip("ملف TXT غير موجود")

        # استخراج من PDF
        pdf_extractor = PDFStructuralExtractor()
        pdf_result = pdf_extractor.extract(pdf_path)

        # قراءة من TXT (للتحقق من التوافق)
        txt_content = txt_path.read_text(encoding='utf-8')
        assert str(pdf_result.serial) in txt_content
