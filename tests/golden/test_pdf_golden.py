import pytest
from pathlib import Path
import fitz  # PyMuPDF

class TestPDFGolden:
    """
    Golden Master Tests لتقارير PDF.
    """
    OUTPUT_DIR = Path("data/output")

    @pytest.mark.parametrize("pdf_name", [
        "visual_test_official.pdf",
        "visual_test_tech.pdf",
    ])
    def test_pdf_structure_and_text(self, pdf_name):
        pdf_path = self.OUTPUT_DIR / pdf_name
        if not pdf_path.exists():
            pytest.skip(f"التقرير {pdf_name} لم يتم توليده بعد")

        doc = fitz.open(str(pdf_path))
        assert len(doc) >= 1, "الملف فارغ"
        
        # التحقق من وجود كلمات مفتاحية (Arabic & English)
        all_text = ""
        for page in doc:
            all_text += page.get_text()
        doc.close()

        # التحقق من SSOT في التقرير
        assert "SSOT" in all_text or "مطابقة" in all_text
        # التحقق من وجود جودة البيانات
        assert "quality" in all_text.lower() or "جودة" in all_text
        assert len(all_text) > 100, "النص المستخرج قليل جداً"