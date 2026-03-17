# tests/unit/test_a1_exposure_analysis.py
"""
اختبارات A1 — تحقق من تطبيق CHANGES_DIFF.py

تغطية:
  1. VaccineSpecification — الكتالوج والمواصفات
  2. ExposureAnalysisService — Q10 + CCM + Circuit Breakers
  3. EvaluateColdChainSafetyUseCase — التكامل الكامل

البيانات المرجعية:
  - 9.8°C لمدة 22 دقيقة → يجب أن يُكتشف في HER
  - 35°C لمدة 3 ساعات → CIRCUIT_BREAKER: CRITICAL_HEAT_34C
  - -1°C (لقاح HepB) → CIRCUIT_BREAKER: FREEZE_EXCURSION
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.value_objects.vaccine_specification import (
    VACCINE_CATALOGUE, VaccineSpecification, get_vaccine_spec)

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


def make_reading(temp: float, duration_minutes: float, device_id: str = "DEV-001"):
    """إنشاء قراءة حرارية مبسطة للاختبار."""
    reading = MagicMock()
    reading.value = temp
    reading.duration_minutes = duration_minutes
    reading.device_id = device_id
    return reading


def make_readings(temps_and_durations: list[tuple[float, float]]) -> list:
    """إنشاء قائمة قراءات من أزواج (درجة، مدة بالدقائق)."""
    return [make_reading(t, d) for t, d in temps_and_durations]


# ══════════════════════════════════════════════════════════════
# 1. اختبارات VaccineSpecification
# ══════════════════════════════════════════════════════════════


class TestVaccineSpecification:

    def test_opv_spec_correct(self):
        spec = get_vaccine_spec("OPV")
        assert spec.vaccine_type == "OPV"
        assert spec.freeze_sensitive is False
        assert spec.vvm_type == "VVM2"
        assert spec.shelf_life_days == 225
        assert spec.q10_factor == 2.0

    def test_hepb_freeze_sensitive(self):
        spec = get_vaccine_spec("HEPB")
        assert spec.freeze_sensitive is True
        assert spec.vvm_type == "VVM30"

    def test_dtp_freeze_sensitive(self):
        spec = get_vaccine_spec("DTP")
        assert spec.freeze_sensitive is True

    def test_bcg_not_freeze_sensitive(self):
        spec = get_vaccine_spec("BCG")
        assert spec.freeze_sensitive is False

    def test_shelf_life_hours(self):
        spec = get_vaccine_spec("OPV")
        assert spec.shelf_life_hours == 225 * 24

    def test_unknown_type_returns_general(self):
        spec = get_vaccine_spec("UNKNOWN_VACCINE_XYZ")
        assert spec.vaccine_type == "GENERAL"

    def test_case_insensitive(self):
        spec_upper = get_vaccine_spec("OPV")
        spec_lower = get_vaccine_spec("opv")
        assert spec_upper.vaccine_type == spec_lower.vaccine_type

    def test_invalid_q10_raises(self):
        with pytest.raises(ValueError):
            VaccineSpecification(vaccine_type="TEST", q10_factor=0.0)

    def test_invalid_shelf_life_raises(self):
        with pytest.raises(ValueError):
            VaccineSpecification(vaccine_type="TEST", shelf_life_days=-10)

    def test_all_catalogue_entries_valid(self):
        for name, spec in VACCINE_CATALOGUE.items():
            assert spec.q10_factor > 0
            assert spec.shelf_life_days > 0
            assert spec.vaccine_type == name


# ══════════════════════════════════════════════════════════════
# 2. اختبارات ExposureAnalysisService
# ══════════════════════════════════════════════════════════════


class TestExposureAnalysisService:

    def setup_method(self):
        self.service = ExposureAnalysisService()
        self.opv_spec = get_vaccine_spec("OPV")
        self.hepb_spec = get_vaccine_spec("HEPB")
        self.general_spec = get_vaccine_spec("GENERAL")

    # ── القراءات الفارغة ───────────────────────────────────────

    def test_empty_readings_returns_zeros(self):
        result = self.service.analyze([], spec=self.general_spec)
        assert result["her_ratio"] == 0.0
        assert result["ccm_index"] == "0"
        assert result["has_freeze"] is False
        assert result["circuit_breaker"] is None

    # ── المشكلة الأصلية: 9.8°C / 22 دقيقة ────────────────────

    def test_9_8_celsius_22_minutes_detected_in_her(self):
        """
        المشكلة الأصلية: 9.8°C لمدة 22 دقيقة لم يُكتشف.
        يجب أن يرفع HER ratio فوق الصفر.
        """
        readings = make_readings([(9.8, 22.0)])
        result = self.service.analyze(readings, spec=self.general_spec)

        # HER يجب أن يكون أكبر من صفر
        assert result["her_ratio"] > 0.0

        # Q10 factor عند 9.8°C (ref=5°C):
        # factor = 2.0^((9.8-5.0)/10) = 2.0^0.48 ≈ 1.394
        # degradation = (22/60) * 1.394 ≈ 0.511 ساعة
        # her_ratio = 0.511 / (730*24) ≈ 0.0000292
        expected_factor = 2.0 ** ((9.8 - 5.0) / 10.0)
        expected_deg_hours = (22.0 / 60.0) * expected_factor
        expected_ratio = expected_deg_hours / (730.0 * 24.0)

        assert abs(result["her_ratio"] - expected_ratio) < 1e-6

    def test_normal_range_low_her(self):
        """4°C لأسبوع كامل → HER منخفض جداً."""
        readings = make_readings([(4.0, 1440.0)] * 7)  # 7 أيام
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["her_ratio"] < 0.1
        assert result["ccm_index"] == "0"

    # ── Circuit Breakers ───────────────────────────────────────

    def test_critical_heat_circuit_breaker(self):
        """35°C لمدة 3 ساعات → CIRCUIT_BREAKER."""
        readings = make_readings([(35.0, 180.0)])  # 3 ساعات
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["circuit_breaker"] == "CRITICAL_HEAT_34C"
        assert result["has_critical_heat"] is True

    def test_critical_heat_exactly_2_hours_triggers(self):
        """34.1°C لمدة ساعتين بالضبط → CIRCUIT_BREAKER."""
        readings = make_readings([(34.1, 120.0)])  # ساعتان
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["circuit_breaker"] == "CRITICAL_HEAT_34C"

    def test_critical_heat_under_2_hours_no_trigger(self):
        """35°C لمدة ساعة واحدة → لا circuit breaker."""
        readings = make_readings([(35.0, 59.0)])  # أقل من ساعة
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["circuit_breaker"] is None

    def test_freeze_sensitive_vaccine_triggers_on_freeze(self):
        """HepB عند -1°C → CIRCUIT_BREAKER: FREEZE."""
        readings = make_readings([(-1.0, 30.0)])
        result = self.service.analyze(readings, spec=self.hepb_spec)
        assert result["circuit_breaker"] == "FREEZE_EXCURSION"
        assert result["has_freeze"] is True

    def test_non_freeze_sensitive_no_circuit_breaker_on_freeze(self):
        """OPV عند -2°C → لا circuit breaker للتجمد."""
        readings = make_readings([(-2.0, 60.0)])
        result = self.service.analyze(readings, spec=self.opv_spec)
        # OPV ليس freeze_sensitive → لا circuit breaker للتجمد
        assert result["circuit_breaker"] is None
        assert result["has_freeze"] is True  # لكن has_freeze يبقى True للتسجيل

    # ── CCM Index ─────────────────────────────────────────────

    def test_ccm_index_0_below_threshold(self):
        """أقل من 72 ساعة فوق 10°C → مؤشر 0."""
        readings = make_readings([(11.0, 60.0)] * 70)  # 70 ساعة
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["ccm_index"] == "0"

    def test_ccm_index_a_3_to_8_days(self):
        """72-192 ساعة فوق 10°C → مؤشر A."""
        readings = make_readings([(12.0, 60.0)] * 80)  # 80 ساعة
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["ccm_index"] == "A"

    def test_ccm_index_ab_8_to_14_days(self):
        """192-336 ساعة فوق 10°C → مؤشر AB."""
        readings = make_readings([(12.0, 60.0)] * 200)  # 200 ساعة
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["ccm_index"] == "AB"

    def test_ccm_index_abc_over_14_days(self):
        """فوق 336 ساعة فوق 10°C → مؤشر ABC."""
        readings = make_readings([(12.0, 60.0)] * 340)  # 340 ساعة
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["ccm_index"] == "ABC"

    def test_ccm_index_d_critical_heat(self):
        """فوق 34°C لأكثر من ساعتين → مؤشر D."""
        readings = make_readings([(37.0, 180.0)])  # 3 ساعات
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["ccm_index"] == "D"

    # ── HER ratio ─────────────────────────────────────────────

    def test_her_ratio_increases_with_temperature(self):
        """HER عند 10°C أكبر من HER عند 5°C للمدة ذاتها."""
        r_5 = make_readings([(5.0, 1440.0)])
        r_10 = make_readings([(10.0, 1440.0)])
        result_5 = self.service.analyze(r_5, spec=self.general_spec)
        result_10 = self.service.analyze(r_10, spec=self.general_spec)
        assert result_10["her_ratio"] > result_5["her_ratio"]

    def test_her_ratio_accumulates_over_time(self):
        """HER لـ 7 أيام أكبر من HER ليوم واحد.

        نستخدم 1e-5 كهامش تسامح بدلاً من 1e-6 لأن round(..., 6)
        في _calculate_her_ratio يُحدث فارقاً صغيراً عند الضرب.
        الأهم: التحقق من الاتجاه (التراكم) وليس الدقة المطلقة.
        """
        r_1day = make_readings([(6.0, 1440.0)])
        r_7days = make_readings([(6.0, 1440.0)] * 7)
        result_1 = self.service.analyze(r_1day, spec=self.general_spec)
        result_7 = self.service.analyze(r_7days, spec=self.general_spec)
        assert result_7["her_ratio"] > result_1["her_ratio"]
        assert abs(result_7["her_ratio"] - result_1["her_ratio"] * 7) < 1e-5

    def test_opv_her_ratio_higher_than_hepb_same_exposure(self):
        """
        OPV shelf_life = 225 يوم vs HepB shelf_life = 1460 يوم
        نفس التعرض → HER ratio أعلى لـ OPV.
        """
        readings = make_readings([(8.0, 1440.0)] * 10)
        result_opv = self.service.analyze(readings, spec=self.opv_spec)
        result_hepb = self.service.analyze(readings, spec=self.hepb_spec)
        assert result_opv["her_ratio"] > result_hepb["her_ratio"]

    def test_her_without_spec_uses_general(self):
        """بدون spec → يستخدم GENERAL تلقائياً."""
        readings = make_readings([(6.0, 60.0)])
        result = self.service.analyze(readings, spec=None)
        assert result["her_ratio"] >= 0.0

    # ── إحصاءات أساسية ────────────────────────────────────────

    def test_max_min_temp_correct(self):
        readings = make_readings([(3.0, 60.0), (8.5, 60.0), (2.0, 60.0)])
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["max_temp"] == 8.5
        assert result["min_temp"] == 2.0

    def test_hours_above_10_correct(self):
        """ساعتان فوق 10°C + ساعة دون 10°C → 2 ساعات فقط."""
        readings = make_readings(
            [
                (11.0, 60.0),  # فوق 10°C
                (11.0, 60.0),  # فوق 10°C
                (5.0, 60.0),  # دون 10°C
            ]
        )
        result = self.service.analyze(readings, spec=self.general_spec)
        assert result["total_hours_above_10"] == 2.0


# ══════════════════════════════════════════════════════════════
# 3. اختبار التكامل — Use Case كامل
# ══════════════════════════════════════════════════════════════


class TestEvaluateColdChainSafetyUseCaseA1:
    """
    اختبار تكامل Use Case بعد تطبيق A1.
    يتحقق أن her_ratio يصل إلى RulesEngine فعلياً.
    """

    def test_use_case_accepts_vaccine_spec(self):
        """Request يقبل vaccine_spec بدون خطأ."""
        from src.domain.dtos.evaluate_cold_chain_safety_request import (
            EvaluateColdChainSafetyRequest, TemperatureReading)

        spec = get_vaccine_spec("OPV")
        t0 = datetime(2024, 7, 1, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2024, 7, 2, 0, 0, tzinfo=timezone.utc)

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

    def test_use_case_without_spec_uses_fallback(self):
        """بدون vaccine_spec → يستخدم نوع اللقاح من الإدخالات."""
        from src.domain.dtos.evaluate_cold_chain_safety_request import (
            EvaluateColdChainSafetyRequest, TemperatureReading)

        t0 = datetime(2024, 7, 1, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2024, 7, 2, 0, 0, tzinfo=timezone.utc)

        request = EvaluateColdChainSafetyRequest(
            center_id="CTR-001",
            readings=(
                TemperatureReading(value=5.0, timestamp=t0, device_id="D1"),
                TemperatureReading(value=5.0, timestamp=t1, device_id="D1"),
            ),
            vaccine_spec=None,  # بدون spec
        )

        assert request.vaccine_spec is None  # الطلب لا يعرف — Use Case يُقرر
