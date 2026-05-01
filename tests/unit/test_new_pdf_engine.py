"""Unit tests for the new PDFGenerator stub (Phase 1).
"""

import pytest

from src.application.dtos.device_report_dto import (
    DeviceReportDTO,
    ReportDecision,
    VVMStage,
)
from src.infrastructure.adapters.reporting.new_pdf_engine import PDFGenerator
from src.utils.time import utc_now_iso

# determine if WeasyPrint is installed so tests can be skipped gracefully
try:
    import weasyprint  # type: ignore  # noqa: F401

    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


@pytest.fixture(autouse=True)
def skip_if_no_weasyprint():
    if not HAS_WEASYPRINT:
        pytest.skip("WeasyPrint not installed")


def make_dto():
    return DeviceReportDTO(
        device_id="UNIT-001",
        center_id="CTR-001",
        center_name="Test Center",
        temperature_ranges={"min": 2.0, "max": 8.0},
        decision=ReportDecision.SAFE,
        vvm_stage=VVMStage.A,
        vaccine_type="Test",
        total_records=1,
        excursions=[],
        final_status="safe",
        scientific_rationale="unit check",
        generated_at=utc_now_iso(),
    )


def test_generate_returns_bytes():
    gen = PDFGenerator()
    pdf = gen.generate(make_dto())
    assert isinstance(pdf, (bytes, bytearray))
    # when WeasyPrint is available we expect a real document, not a tiny fallback.
    assert len(pdf) > 1000
    assert pdf.startswith(b"%PDF")


def test_generate_with_report_type():
    gen = PDFGenerator()
    pdf = gen.generate(make_dto(), report_type="technical")
    assert pdf.startswith(b'%PDF')


def test_generate_contains_page():
    gen = PDFGenerator()
    pdf = gen.generate(make_dto(), report_type="official")
    assert pdf.startswith(b'%PDF')
    assert pdf_bytes.startswith(b'%PDF')
    assert len(pdf_bytes) > 1000  # تأكيد أن الـ PDF فيه محتوى حقيقي
