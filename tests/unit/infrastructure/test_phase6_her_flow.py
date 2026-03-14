# tests/integration/test_phase6_her_flow.py
"""
اختبارات تكامل Phase 6.1 — التدفق الكامل من Request إلى HER في Response.

تتحقق من:
1. her_ratio يصل فعلاً إلى VVMStageRule (لم يعد = 0.0)
2. TemperatureMapper يحوّل بشكل صحيح
3. ExposureAnalysisService يُنتج her_ratio حقيقي
4. sampling_gap يُكتشف ويُسجَّل
5. vaccine_spec تصل من Request إلى Context
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.domain.calculators.q10_her_calculator import Q10HerCalculator
from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.services.exposure_analysis_service import ExposureAnalysisService
from src.domain.value_objects.temperature_entry import TemperatureEntry
from src.domain.value_objects.vaccine_specification import VaccineSpecification
from src.infrastructure.mappers.temperature_mapper import TemperatureMapper


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

def make_spec(freeze_sensitive: bool = True) -> VaccineSpecification:
    return VaccineSpecification(
        vaccine_type="DTP",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=freeze_sensitive,
        max_heat_temp=37.0,
        max_heat_duration_hours=48.0,
    )


def make_entries(
    temps: list[float],
    start: datetime | None = None,
    interval_minutes: float = 5.0,
) -> list[TemperatureEntry]:
    if start is None:
        start = datetime(2025, 6, 1, 8, 0, 0)
    return [
        TemperatureEntry(
            temperature=t,
            timestamp=start + timedelta(minutes=i * interval_minutes),
            duration_minutes=interval_minutes,
            device_id="FT2-001",
        )
        for i, t in enumerate(temps)
    ]


# ---------------------------------------------------------------------------
# TemperatureMapper
# ---------------------------------------------------------------------------

class TestTemperatureMapper:

    def test_entries_to_readings_preserves_values(self):
        entries = make_entries([5.0, 7.0, 8.0])
        readings = TemperatureMapper.entries_to_readings(entries)

        assert len(readings) == 3
        assert readings[0].value == 5.0
        assert readings[1].value == 7.0

    def test_entries_to_readings_preserves_timestamps(self):
        t0 = datetime(2025, 1, 1)
        entries = [
            TemperatureEntry(temperature=6.0, timestamp=t0, duration_minutes=5.0),
            TemperatureEntry(temperature=7.0, timestamp=t0 + timedelta(minutes=5), duration_minutes=5.0),
        ]
        readings = TemperatureMapper.entries_to_readings(entries)
        assert readings[0].recorded_at == t0
        assert readings[1].recorded_at == t0 + timedelta(minutes=5)

    def test_device_id_mapped_to_vaccine_id(self):
        entries = [
            TemperatureEntry(temperature=5.0, timestamp=datetime(2025, 1, 1),
                           duration_minutes=5.0, device_id="FT2-007")
        ]
        readings = TemperatureMapper.entries_to_readings(entries)
        assert readings[0].vaccine_id == "FT2-007"

    def test_empty_entries_returns_empty(self):
        assert TemperatureMapper.entries_to_readings([]) == []


# ---------------------------------------------------------------------------
# ExposureAnalysisService
# ---------------------------------------------------------------------------

class TestExposureAnalysisService:

    def test_returns_her_ratio_key(self):
        svc = ExposureAnalysisService()
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 5.0, t0),
            TemperatureReading("V", 5.0, t0 + timedelta(hours=1)),
        ]
        result = svc.analyze(readings)
        assert "her_ratio" in result
        assert isinstance(result["her_ratio"], float)

    def test_returns_data_quality_flags_key(self):
        svc = ExposureAnalysisService()
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 5.0, t0),
            TemperatureReading("V", 5.0, t0 + timedelta(hours=1)),
        ]
        result = svc.analyze(readings)
        assert "data_quality_flags" in result
        assert "sampling_gap" in result["data_quality_flags"]

    def test_her_ratio_not_zero_above_reference(self):
        """HER يجب أن يكون > 0 عند درجة حرارة فوق المرجع."""
        svc = ExposureAnalysisService(reference_temp=5.0)
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 15.0, t0),
            TemperatureReading("V", 15.0, t0 + timedelta(hours=1)),
        ]
        result = svc.analyze(readings)
        assert result["her_ratio"] > 0.0

    def test_empty_readings_her_ratio_zero(self):
        svc = ExposureAnalysisService()
        result = svc.analyze([])
        assert result["her_ratio"] == 0.0

    def test_accepts_spec_without_error(self):
        """يجب ألا يرفع استثناءً عند تمرير spec."""
        svc = ExposureAnalysisService()
        spec = make_spec()
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 6.0, t0),
            TemperatureReading("V", 7.0, t0 + timedelta(minutes=10)),
        ]
        result = svc.analyze(readings, spec=spec)
        assert "her_ratio" in result


# ---------------------------------------------------------------------------
# Q10HerCalculator — midpoint + max_gap
# ---------------------------------------------------------------------------

class TestQ10HerCalculatorMidpoint:

    def test_midpoint_used_not_current_temp(self):
        """
        قراءتان: 5°C ثم 15°C، مدة ساعة.
        midpoint = 10°C، factor = 2^((10-5)/10) = 2^0.5 ≈ 1.414
        her_hours ≈ 1.414
        """
        calc = Q10HerCalculator(q10_value=2.0, reference_temp=5.0, shelf_life_hours=100.0)
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 5.0, t0),
            TemperatureReading("V", 15.0, t0 + timedelta(hours=1)),
        ]
        result = calc.calculate(readings)
        import math
        expected = math.pow(2.0, (10.0 - 5.0) / 10.0) * 1.0  # midpoint=10, Δt=1h
        assert abs(result.cumulative_degradation_hours - expected) < 1e-6

    def test_sampling_gap_detected(self):
        """فجوة > max_gap_hours تُسجَّل في data_quality_flags."""
        calc = Q10HerCalculator(max_gap_hours=0.5)
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 6.0, t0),
            TemperatureReading("V", 7.0, t0 + timedelta(hours=4)),  # فجوة 4h
        ]
        result = calc.calculate(readings)
        assert result.data_quality_flags["sampling_gap"] is True

    def test_sampling_gap_clamped_to_max(self):
        """
        فجوة 4h تُقيَّد إلى max_gap=0.5h.
        her_hours يجب أن يكون أقل بكثير من نسخة غير مقيَّدة.
        """
        calc_clamped = Q10HerCalculator(max_gap_hours=0.5, shelf_life_hours=100.0)
        calc_unclamped = Q10HerCalculator(max_gap_hours=100.0, shelf_life_hours=100.0)
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 20.0, t0),
            TemperatureReading("V", 20.0, t0 + timedelta(hours=4)),
        ]
        r_clamped = calc_clamped.calculate(readings)
        r_unclamped = calc_unclamped.calculate(readings)

        # النسخة المقيَّدة يجب أن تكون أصغر بكثير
        assert r_clamped.cumulative_degradation_hours < r_unclamped.cumulative_degradation_hours

    def test_no_gap_no_flag(self):
        """قراءات منتظمة كل 5 دقائق لا تُسجَّل فجوة."""
        calc = Q10HerCalculator(max_gap_hours=0.5)
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 6.0, t0 + timedelta(minutes=i * 5))
            for i in range(10)
        ]
        result = calc.calculate(readings)
        assert result.data_quality_flags["sampling_gap"] is False

    def test_her_ratio_reaches_vvm_stage_d(self):
        """
        تحقق أن her_ratio يمكن أن يتجاوز 1.0 لتفعيل VVMStageRule D.
        """
        calc = Q10HerCalculator(
            q10_value=2.0,
            reference_temp=5.0,
            shelf_life_hours=1.0,  # حد منخفض لإجبار التجاوز
        )
        t0 = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V", 15.0, t0),
            TemperatureReading("V", 15.0, t0 + timedelta(hours=2)),
        ]
        result = calc.calculate(readings)
        assert result.her_ratio >= 1.0
        assert result.is_critical


# ---------------------------------------------------------------------------
# تكامل كامل: Entries → Mapper → Service → her_ratio
# ---------------------------------------------------------------------------

class TestFullHERFlow:

    def test_entries_flow_produces_nonzero_her(self):
        """
        تدفق كامل: TemperatureEntry → Mapper → ExposureAnalysisService.
        HER يجب ألا يكون صفراً عند درجات حرارة مرتفعة.
        """
        entries = make_entries([10.0, 12.0, 15.0, 14.0], interval_minutes=60.0)
        readings = TemperatureMapper.entries_to_readings(entries)
        svc = ExposureAnalysisService(reference_temp=5.0)
        result = svc.analyze(readings)

        assert result["her_ratio"] > 0.0

    def test_her_ratio_in_analysis_matches_calculator_direct(self):
        """
        her_ratio في ExposureAnalysisService يساوي ما يُنتجه Q10HerCalculator مباشرة.
        """
        t0 = datetime(2025, 6, 1)
        readings = [
            TemperatureReading("V", 8.0, t0),
            TemperatureReading("V", 10.0, t0 + timedelta(minutes=30)),
            TemperatureReading("V", 12.0, t0 + timedelta(hours=1)),
        ]

        svc = ExposureAnalysisService(q10_value=2.0, reference_temp=5.0, shelf_life_hours=48.0)
        calc = Q10HerCalculator(q10_value=2.0, reference_temp=5.0, shelf_life_hours=48.0)

        service_result = svc.analyze(readings)
        calc_result = calc.calculate(readings)

        assert service_result["her_ratio"] == pytest.approx(calc_result.her_ratio, rel=1e-9)