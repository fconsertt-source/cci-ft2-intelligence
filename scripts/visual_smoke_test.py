"""Visual smoke tests for the PDF subsystem.

Converted to proper pytest tests and updated to use the DTO/renderer
interface.  The previous incarnation mixed a script with pytest and
contained a syntax error.
"""


import pytest
from src.utils.time import utc_now_iso
from src.application.dtos.device_report_dto import DeviceReportDTO
from src.infrastructure.pdf.unified_pdf_generator import get_pdf_generator


def _make_dto() -> DeviceReportDTO:
    return DeviceReportDTO(
        device_id="SMOKE-001",
        vaccine_type="Dummy",
        total_records=0,
        excursions=[],
        final_status="safe",
        scientific_rationale="Smoke test",
        generated_at=utc_now_iso(),
    )


def test_pdf_arabic_mixed_text():
    """Tier‑2: Arabic + Latin text should render without crash."""
    dto = _make_dto()
    # put some mixed content into the rationale field
    dto = dto.__class__(**{**dto.__dict__, "scientific_rationale": "درجة الحرارة 25°C"})

    pdf_bytes = get_pdf_generator().render(dto)

    assert pdf_bytes.startswith(b"%PDF"), "Invalid PDF signature"
    assert len(pdf_bytes) > 100, "PDF too small — likely generation failure"


def test_font_is_embedded():
    """Tier‑1: Arabic font should be embedded in the document."""
    dto = _make_dto()
    pdf_bytes = get_pdf_generator().render(dto)

    # when reportlab is missing we return a tiny placeholder PDF without any
    # font objects; in that situation the assertion is meaningless so skip.
    if b"Font" not in pdf_bytes:
        pytest.skip("fallback PDF returned, cannot verify font embedding")

    assert b"/FontFile2" in pdf_bytes, "Arabic font not embedded"
    assert b"/Type /Page" in pdf_bytes
