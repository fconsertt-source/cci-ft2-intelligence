#!/usr/bin/env python3
"""اختبارات تكامل لتوليد التقارير المرئية فعلياً"""

import pytest

# skip the whole module if heavy dependencies aren't available
try:
    import pandas  # noqa: F401
    import reportlab  # noqa: F401
except ImportError:
    pytest.skip(
        "Skipping visual report generation integration tests - missing dependencies",
        allow_module_level=True,
    )


@pytest.mark.integration
def test_generate_all_three_pdfs(tmp_path):
    """يتأكد من توليد الملفات الثلاثة فعلياً"""
    from scripts.verify_visual_reports import generate_visual_reports

    output_dir = tmp_path / "visual_tests"
    generate_visual_reports(output_dir=str(output_dir))

    # تحقق من الوجود
    assert (output_dir / "visual_test_official.pdf").exists()
    assert (output_dir / "visual_test_arabic.pdf").exists()
    assert (output_dir / "visual_test_tech.pdf").exists()
    assert (output_dir / "temp_dist.png").exists()

    # تحقق من الحجم (ليس فارغاً)
    for file in output_dir.glob("*"):
        assert file.stat().st_size > 0, f"{file} is empty"


@pytest.mark.integration
def test_pdf_pages_exist(tmp_path):
    """فحص عدد الصفحات الأساسي"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        pytest.skip("PyPDF2 not installed")

    from scripts.verify_visual_reports import generate_visual_reports

    output_dir = tmp_path / "visual_tests"
    generate_visual_reports(output_dir=str(output_dir))

    pdf_path = output_dir / "visual_test_official.pdf"
    reader = PdfReader(str(pdf_path))

    assert len(reader.pages) >= 1, "PDF should have at least 1 page"


@pytest.mark.integration
def test_chart_image_exists(tmp_path):
    """يتأكد من وجود الرسم البياني"""
    from scripts.verify_visual_reports import generate_visual_reports

    output_dir = tmp_path / "visual_tests"
    generate_visual_reports(output_dir=str(output_dir))

    chart_path = output_dir / "temp_dist.png"
    assert chart_path.exists()
    assert chart_path.stat().st_size > 0
