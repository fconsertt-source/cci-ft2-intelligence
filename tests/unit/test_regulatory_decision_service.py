# tests/unit/test_regulatory_decision_service.py
"""
اختبارات وحدة لـ RegulatoryDecisionService.

كل اختبار مرتبط بقاعدة تنظيمية محددة.
المرجع: WHO/IVB/06.10
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.value_objects.vaccine_specification import VaccineSpecification

# ---------------------------------------------------------------------------
# helpers — بناء specs بسرعة
# ---------------------------------------------------------------------------


def make_spec(
    min_temp: float = 2.0,
    max_temp: float = 8.0,
    max_heat_temp: float | None = None,
    max_heat_duration_hours: float | None = 2.0,
    freeze_sensitive: bool = True,
    freeze_range: tuple[float, float] | None = None,
) -> VaccineSpecification:
    """Mock لـ VaccineSpecification بالقيم المطلوبة فقط."""
    spec = MagicMock(spec=VaccineSpecification)
    spec.min_temp = min_temp
    spec.max_temp = max_temp
    spec.max_heat_temp = max_heat_temp
    spec.max_heat_duration_hours = max_heat_duration_hours
    spec.freeze_sensitive = freeze_sensitive
    spec.freeze_range = freeze_range
    return spec


SVC = RegulatoryDecisionService()


# ===========================================================================
# FREEZE SENSITIVE VACCINES — DTP, TT, HepB, Hib liquid
# المصدر: WHO/IVB/06.10 §5.2, §6.2, §3
# ===========================================================================


class TestFreezeSensitiveVaccines:

    def test_at_zero_discard(self):
        """0°C = تجميد = DISCARD فوري."""
        spec = make_spec(freeze_sensitive=True)
        assert SVC.evaluate(0.0, 10.0, spec) == "DISCARD"

    def test_below_zero_discard(self):
        """-5°C = تجميد = DISCARD."""
        spec = make_spec(freeze_sensitive=True)
        assert SVC.evaluate(-5.0, 5.0, spec) == "DISCARD"

    def test_well_below_zero_discard(self):
        """-20°C = تجميد = DISCARD."""
        spec = make_spec(freeze_sensitive=True)
        assert SVC.evaluate(-20.0, 60.0, spec) == "DISCARD"

    def test_just_above_zero_not_discard_by_freeze(self):
        """0.1°C ≠ تجميد — يُتابع الفحص للحرارة."""
        spec = make_spec(
            freeze_sensitive=True, max_temp=8.0, max_heat_duration_hours=2.0
        )
        result = SVC.evaluate(0.1, 10.0, spec)
        # ليس تجميداً — يجب أن يكون SAFE (ضمن النطاق)
        assert result == "SAFE"

    def test_freeze_discard_regardless_of_duration(self):
        """قاعدة التجميد مطلقة — المدة لا تهم."""
        spec = make_spec(freeze_sensitive=True)
        assert SVC.evaluate(-1.0, 1.0, spec) == "DISCARD"
        assert SVC.evaluate(-1.0, 1000.0, spec) == "DISCARD"


# ===========================================================================
# FREEZE STABLE WITH FREEZE RANGE — OPV, BCG, Measles, YF
# المصدر: WHO/IVB/06.10 §12.2 (OPV يُحفظ عند -15 إلى -25°C)
# ===========================================================================


class TestFreezeStableWithFreezeRange:

    def test_within_freeze_range_safe(self):
        """ضمن نطاق التجميد المسموح = SAFE."""
        spec = make_spec(
            freeze_sensitive=False,
            freeze_range=(-25.0, -15.0),
            max_temp=8.0,
        )
        assert SVC.evaluate(-20.0, 60.0, spec) == "SAFE"
        assert SVC.evaluate(-15.0, 60.0, spec) == "SAFE"
        assert SVC.evaluate(-25.0, 60.0, spec) == "SAFE"

    def test_outside_freeze_range_below_zero_discard(self):
        """تجميد خارج النطاق المسموح = DISCARD."""
        spec = make_spec(
            freeze_sensitive=False,
            freeze_range=(-25.0, -15.0),
        )
        assert SVC.evaluate(-30.0, 10.0, spec) == "DISCARD"
        assert SVC.evaluate(-5.0, 10.0, spec) == "DISCARD"

    def test_freeze_stable_no_range_below_zero_discard(self):
        """لقاح غير حساس بدون freeze_range + تجميد = DISCARD."""
        spec = make_spec(freeze_sensitive=False, freeze_range=None)
        assert SVC.evaluate(-5.0, 10.0, spec) == "DISCARD"


# ===========================================================================
# MAX HEAT TEMP — الحد الأقصى المطلق
# المصدر: WHO/IVB/06.10 §5.1 "At 60°C destroyed in 3-5 hours"
# ===========================================================================


class TestMaxHeatTempAbsoluteLimit:

    def test_exceeds_max_heat_temp_discard_immediately(self):
        """تجاوز max_heat_temp = DISCARD فوري بغض النظر عن المدة."""
        spec = make_spec(max_temp=8.0, max_heat_temp=37.0, max_heat_duration_hours=48.0)
        assert SVC.evaluate(38.0, 1.0, spec) == "DISCARD"
        assert SVC.evaluate(38.0, 0.1, spec) == "DISCARD"

    def test_exactly_at_max_heat_temp_not_discard_by_this_rule(self):
        """بالضبط = max_heat_temp لا يُفعّل هذه القاعدة (تستخدم >)."""
        spec = make_spec(max_temp=8.0, max_heat_temp=37.0, max_heat_duration_hours=48.0)
        # 37.0 = max_heat_temp → لا تُفعّل DISCARD هنا
        # لكن > max_temp (8.0) → يذهب لفحص المدة
        result = SVC.evaluate(37.0, 1.0, spec)
        assert result == "PARTIAL"

    def test_no_max_heat_temp_falls_back_to_max_temp(self):
        """إذا لم يوجد max_heat_temp، يستخدم max_temp كبديل."""
        spec = make_spec(max_temp=8.0, max_heat_temp=None, max_heat_duration_hours=2.0)
        # temperature > max_temp (8.0) → يستخدم max_temp كـ max_heat_temp
        # 9.0 > 8.0 → لكن < 8.0 (الحد المستخدم) = خطأ في المنطق
        # في الواقع: max_heat_temp = None → fallback = max_temp = 8.0
        # 9.0 > 8.0 → DISCARD فوري عند max_heat_temp check
        result = SVC.evaluate(9.0, 0.5, spec)
        # 9.0 > max_heat_temp(8.0) → DISCARD
        assert result == "DISCARD"


# ===========================================================================
# HEAT DURATION CHECK — PARTIAL vs DISCARD
# المصدر: WHO/IVB/06.10 §5.1 Table 2
# ===========================================================================


class TestHeatDurationCheck:

    def test_above_max_temp_within_duration_partial(self):
        """
        تجاوز max_temp لكن المدة ضمن الحد = PARTIAL.
        مثال: HepB عند 37°C لأقل من أسبوع = PARTIAL.
        """
        spec = make_spec(
            max_temp=8.0,
            max_heat_temp=37.0,
            max_heat_duration_hours=48.0,
        )
        # 25°C > 8.0, 1 ساعة < 48 ساعة
        assert SVC.evaluate(25.0, 60.0, spec) == "PARTIAL"

    def test_above_max_temp_exceeds_duration_discard(self):
        """تجاوز max_temp ومدة الحد = DISCARD."""
        spec = make_spec(
            max_temp=8.0,
            max_heat_temp=37.0,
            max_heat_duration_hours=2.0,
        )
        # 25°C > 8.0, 180 min = 3h > 2h
        assert SVC.evaluate(25.0, 180.0, spec) == "DISCARD"

    def test_exactly_at_duration_limit_discard(self):
        """عند الحد بالضبط = DISCARD (استخدم >=)."""
        spec = make_spec(
            max_temp=8.0,
            max_heat_temp=37.0,
            max_heat_duration_hours=2.0,
        )
        # 120 min = 2h = max_heat_duration_hours
        assert SVC.evaluate(25.0, 120.0, spec) == "DISCARD"

    def test_no_duration_limit_defined_discard_immediately(self):
        """إذا لم تُحدَّد مدة، أي تجاوز = DISCARD فوري."""
        spec = make_spec(
            max_temp=8.0,
            max_heat_temp=37.0,
            max_heat_duration_hours=None,
        )
        # max_heat_duration_hours = None → or 0.0 → 0.0 min >= 0h → DISCARD
        assert SVC.evaluate(25.0, 1.0, spec) == "DISCARD"


# ===========================================================================
# SAFE — ضمن النطاق الطبيعي
# ===========================================================================


class TestSafeWithinRange:

    def test_within_normal_range_safe(self):
        """ضمن نطاق 2-8°C = SAFE."""
        spec = make_spec(min_temp=2.0, max_temp=8.0)
        assert SVC.evaluate(5.0, 60.0, spec) == "SAFE"
        assert SVC.evaluate(2.0, 60.0, spec) == "SAFE"
        assert SVC.evaluate(8.0, 60.0, spec) == "SAFE"

    def test_exactly_at_max_temp_safe(self):
        """بالضبط = max_temp لا يُفعّل فحص الحرارة (يستخدم >)."""
        spec = make_spec(max_temp=8.0)
        assert SVC.evaluate(8.0, 600.0, spec) == "SAFE"

    def test_long_duration_within_range_still_safe(self):
        """مدة طويلة ضمن النطاق = SAFE دائماً."""
        spec = make_spec(max_temp=8.0)
        assert SVC.evaluate(5.0, 10_000.0, spec) == "SAFE"


# ===========================================================================
# OUTCOME CONTRACT — نتائج محدودة بـ 3 فقط
# ===========================================================================


class TestOutcomeContract:

    @pytest.mark.parametrize(
        "temp,duration,expected",
        [
            (-5.0, 10.0, "DISCARD"),  # تجميد مؤذٍ
            (5.0, 60.0, "SAFE"),  # طبيعي
            (25.0, 30.0, "PARTIAL"),  # تجاوز مؤقت
            (50.0, 1.0, "DISCARD"),  # تجاوز max_heat_temp
            (25.0, 180.0, "DISCARD"),  # تجاوز مدة
        ],
    )
    def test_outcome_is_one_of_three(self, temp, duration, expected):
        spec = make_spec(
            max_temp=8.0,
            max_heat_temp=37.0,
            max_heat_duration_hours=2.0,
            freeze_sensitive=True,
        )
        result = SVC.evaluate(temp, duration, spec)
        assert result in ("SAFE", "PARTIAL", "DISCARD")
        assert result == expected

    def test_no_probabilistic_fields_used(self):
        """التحقق من أن الكود لا يستدعي Q10 أو HER أو CCM."""
        import importlib
        import sys

        mod_name = "src.domain.services.regulatory_decision_service"
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
        else:
            mod = importlib.import_module(mod_name)

        with open(mod.__file__) as f:
            source = f.read().lower()

        forbidden = [
            "q10",
            "her_calculator",
            "ccm_calculator",
            "vvmq10model",
            "math.pow",
            "math.log",
            "probability",
            "estimate",
        ]
        for term in forbidden:
            assert (
                term not in source
            ), f"وُجد '{term}' في regulatory service — مخالف للمبدأ"
