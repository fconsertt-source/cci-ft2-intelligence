"""
اختبارات A1 — تحقق من تطبيق CHANGES_DIFF.py (v2 Clean)
تغطية:
VaccineSpecification
ExposureAnalysisService (Q10 + CCM + Circuit Breakers)
EvaluateColdChainSafetyUseCase (integration)

الإصدار: 2.0 - v2 architecture aligned
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.value_objects.vaccine_specification import VaccineSpecification
from tests.builders.vaccine_spec_builder import build_spec

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def make_reading(temp: float, duration_minutes: float, device_id: str = "DEV-001"):
    reading = MagicMock()
    reading.value = temp
    reading.duration_minutes = duration_minutes
    reading.device_id = device_id
    return reading


def make_readings(temps_and_durations: list[tuple[float, float]]) -> list:
    return [make_reading(t, d) for t, d in temps_and_durations]


# ═══════════════════════════════════════════════════════════════
# 1. VaccineSpecification
# ═══════════════════════════════════════════════════════════════


class TestVaccineSpecification:

    def test_opv_spec_correct(self):
        spec = build_spec(name="OPV")

        assert spec.vaccine_type == "OPV"
        assert spec.freeze_sensitive is False
        assert spec.vvm_type == "VVM2"
        assert spec.shelf_life_days == 126
        assert spec.q10_factor == 3.6
        assert spec.reference_temp_c == 5.0
        assert spec.critical_temp_c == 34.0
        assert spec.critical_hours == 2.0

    def test_hepb_freeze_sensitive(self):
        spec = build_spec(name="HEPB")
        assert spec.freeze_sensitive is True

    def test_dtp_freeze_sensitive(self):
        spec = build_spec(name="DTP")
        assert spec.freeze_sensitive is True

    def test_bcg_not_freeze_sensitive(self):
        spec = build_spec(name="BCG")
        assert spec.freeze_sensitive is False

    def test_unknown_type_returns_general(self):
        spec = build_spec(name="UNKNOWN_VACCINE_XYZ")
        assert spec.vaccine_type == "GENERAL"

    def test_case_insensitive(self):
        spec_upper = build_spec(name="OPV")
        spec_lower = build_spec(name="opv")
        assert spec_upper.vaccine_type == spec_lower.vaccine_type

    def test_invalid_q10_raises(self):
        with pytest.raises(ValueError):
            VaccineSpecification(
                vaccine_type="TEST",
                q10_factor=0.0,
                shelf_life_days=100,
            )

    def test_invalid_shelf_life_raises(self):
        with pytest.raises(ValueError):
            VaccineSpecification(
                vaccine_type="TEST",
                q10_factor=2.0,
                shelf_life_days=-10,
            )


# ═══════════════════════════════════════════════════════════════
# 2. ExposureAnalysisService
# ═══════════════════════════════════════════════════════════════


class TestExposureAnalysisService:

    def setup_method(self):
        self.service = ExposureAnalysisService()
        self.opv_spec = build_spec(name="OPV")
        self.hepb_spec = build_spec(name="HEPB")
        self.general_spec = build_spec(name="GENERAL")

    def test_empty_readings_returns_zeros(self):
        result = self.service.analyze([], spec=self.general_spec)

        assert result["her_ratio"] == 0.0
        assert result["ccm_index"] == "0"
        assert result["has_freeze"] is False
        assert result["circuit_breaker"] is None

    def test_9_8_celsius_detected_in_her(self):
        readings = make_readings([(9.8, 22.0)])
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["her_ratio"] > 0.0

    def test_normal_range_low_her(self):
        readings = make_readings([(4.0, 1440.0)] * 7)
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["her_ratio"] < 0.1
        assert result["ccm_index"] == "0"

    def test_critical_heat_circuit_breaker(self):
        readings = make_readings([(35.0, 180.0)])
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["circuit_breaker"] == "CRITICAL_HEAT_34C"
        assert result["has_critical_heat"] is True

    def test_critical_heat_under_2_hours_no_trigger(self):
        readings = make_readings([(35.0, 59.0)])
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["circuit_breaker"] is None

    def test_freeze_sensitive_triggers(self):
        readings = make_readings([(-1.0, 30.0)])
        result = self.service.analyze(readings, spec=self.hepb_spec)

        assert result["circuit_breaker"] == "FREEZE_EXCURSION"
        assert result["has_freeze"] is True

    def test_non_freeze_sensitive_no_circuit_breaker_on_freeze(self):
        readings = make_readings([(-2.0, 60.0)])
        result = self.service.analyze(readings, spec=self.opv_spec)

        assert result["has_freeze"] is True
        assert result["circuit_breaker"] is None

    def test_ccm_index_calculation(self):
        readings = make_readings([(11.0, 60.0)] * 80)
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["ccm_index"] in ["A", "AB", "ABC"]

    def test_her_ratio_increases_with_temperature(self):
        r1 = make_readings([(5.0, 1440.0)])
        r2 = make_readings([(10.0, 1440.0)])

        res1 = self.service.analyze(r1, spec=self.general_spec)
        res2 = self.service.analyze(r2, spec=self.general_spec)

        assert res2["her_ratio"] > res1["her_ratio"]

    def test_her_accumulates_over_time(self):
        r1 = make_readings([(6.0, 1440.0)])
        r2 = make_readings([(6.0, 1440.0)] * 7)

        res1 = self.service.analyze(r1, spec=self.general_spec)
        res2 = self.service.analyze(r2, spec=self.general_spec)

        assert res2["her_ratio"] > res1["her_ratio"]

    def test_max_min_temp(self):
        readings = make_readings([(3.0, 60.0), (8.5, 60.0), (2.0, 60.0)])
        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["max_temp"] == 8.5
        assert result["min_temp"] == 2.0

    def test_hours_above_10(self):
        readings = make_readings(
            [
                (11.0, 60.0),
                (11.0, 60.0),
                (5.0, 60.0),
            ]
        )

        result = self.service.analyze(readings, spec=self.general_spec)

        assert result["total_hours_above_10"] == 2.0


# ═══════════════════════════════════════════════════════════════
# 3. Integration Use Case
# ═══════════════════════════════════════════════════════════════


class TestEvaluateColdChainSafetyUseCaseA1:

    def test_request_with_spec(self):
        from src.domain.dtos.evaluate_cold_chain_safety_request import (
            EvaluateColdChainSafetyRequest, TemperatureReading)

        spec = build_spec(name="OPV")

        t0 = datetime(2024, 7, 1, tzinfo=timezone.utc)
        t1 = datetime(2024, 7, 2, tzinfo=timezone.utc)

        request = EvaluateColdChainSafetyRequest(
            center_id="CTR-001",
            center_name="مركز الاختبار",
            readings=(
                TemperatureReading(value=5.0, timestamp=t0, device_id="D1"),
                TemperatureReading(value=5.0, timestamp=t1, device_id="D1"),
            ),
            vaccine_spec=spec,
        )

        assert request.vaccine_spec is not None
        assert request.vaccine_spec.vaccine_type == "OPV"

    def test_request_without_spec(self):
        from src.domain.dtos.evaluate_cold_chain_safety_request import (
            EvaluateColdChainSafetyRequest, TemperatureReading)

        t0 = datetime(2024, 7, 1, tzinfo=timezone.utc)
        t1 = datetime(2024, 7, 2, tzinfo=timezone.utc)

        request = EvaluateColdChainSafetyRequest(
            center_id="CTR-001",
            readings=(
                TemperatureReading(value=5.0, timestamp=t0, device_id="D1"),
                TemperatureReading(value=5.0, timestamp=t1, device_id="D1"),
            ),
            vaccine_spec=None,
        )

        assert request.vaccine_spec is None
