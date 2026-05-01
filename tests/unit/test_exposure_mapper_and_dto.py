# tests/unit/test_exposure_mapper_and_dto.py — الأسطر المُصلَحة فقط
# ضع هذا الكود بدلاً من make_dto و _make_excursion الموجودَين في الملف

# ─── make_dto helper (السطر ~90 في الملف الأصلي) ───────────────────────────
from src.application.dtos.device_report_dto import ReportDecision, DeviceReportDTO, VVMStage, ThermalExcursionDTO

def make_dto(**kwargs):
    defaults = dict(
        device_id="DEV-001",
        # ✅ الحقول الإلزامية الجديدة
        center_id="CTR-001",
        center_name="Test Center",
        temperature_ranges={"min": 2.0, "max": 8.0},
        decision=ReportDecision.SAFE,
        vvm_stage=VVMStage.A,
        # الحقول القديمة
        vaccine_type="Pfizer",
        total_records=10,
        excursions=[],
        final_status="SAFE",
        scientific_rationale="test",
        generated_at=None,          # سيُضبط تلقائياً بـ __post_init__
        ledger_hash="a" * 64,
    )
    defaults.update(kwargs)
    return DeviceReportDTO(**defaults)


# ─── _make_excursion helper (داخل TestDeviceReportDTOGetBatchCounts) ────────
def _make_excursion(impact_level):
    return ThermalExcursionDTO(
        timestamp="2024-01-01T00:00:00",
        # ✅ max_temperature بدلاً من temperature
        max_temperature=10.0,
        min_temperature=None,
        excursion_type="HEAT",
        device_id="DEV-001",
        duration_minutes=60,
        impact_level=impact_level,
        aefi_report_recommended=(impact_level in ("DISCARD", "PARTIAL")),
    )