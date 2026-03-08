"""Ensure PDF strategies successfully produce byte output."""

from datetime import datetime

from src.domain.dtos.device_report_dto import DeviceReportDTO
from src.infrastructure.adapters.reporting.pdf_strategy import (
    ArabicPDFStrategy,
    OfficialPDFStrategy,
    TechnicalPDFStrategy,
)


def make_dto():
    return DeviceReportDTO(
        device_id="STRAT-001",
        vaccine_type="Test",
        total_records=0,
        excursions=[],
        final_status="safe",
        scientific_rationale="Strategy test",
        generated_at=datetime.utcnow().isoformat(),
    )


def test_strategies_generate():
    dto = make_dto()
    for strat_cls in (OfficialPDFStrategy, TechnicalPDFStrategy, ArabicPDFStrategy):
        strat = strat_cls()
        pdf = strat.generate(dto, language="ar")
        assert isinstance(pdf, (bytes, bytearray))
        assert pdf.startswith(b"%PDF")
