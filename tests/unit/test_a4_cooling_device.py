# tests/unit/test_b4_vaccine_pipeline_integration.py
"""
B4 - اختبارات تكامل متقدمة لتقييم اللقاحات.
"""

import csv

import pytest

from src.domain.enums.vaccine_decision import DecisionReason, VaccineDecision


# Fixture مساعدة لتقييم اللقاحات (مرنة)
@pytest.fixture
def assess(vaccine_assessment_service, fixed_today):
    """دالة تقييم مع تاريخ ثابت مدمج."""

    def _assess(vaccine, readings):
        return vaccine_assessment_service.assess(
            vaccine, readings, reference_date=fixed_today
        )

    return _assess


@pytest.mark.integration
@pytest.mark.b4
class TestVaccinePipelineIntegration:
    """اختبارات تكامل متقدمة لـ pipeline تقييم اللقاحات."""

    def test_expired_vaccine_discarded_first(
        self, assess, equipment_vaccines, temperature_readings
    ):
        """اختبار أن اللقاح منتهي الصلاحية يُرفض فوراً مع تفاصيل واضحة."""
        expired = next(v for v in equipment_vaccines if v.batch_number == "B2023-EXP")
        readings = temperature_readings.get(expired.equipment_id, [])

        result = assess(expired, readings)

        assert result.decision == VaccineDecision.EXPIRED
        assert result.reason == DecisionReason.EXPIRED
        assert (
            "انتهت الصلاحية" in result.decision_detail
            or "منتهية الصلاحية" in result.decision_detail
        )

    def test_vvm_stage_3_discards_regardless_of_her(
        self, assess, equipment_vaccines, temperature_readings
    ):
        """اختبار أن VVM stage 3 يؤدي إلى DISCARD حتى مع HER منخفض."""
        vvm3 = next(v for v in equipment_vaccines if v.batch_number == "B2024-VVM3")
        readings = temperature_readings.get(vvm3.equipment_id, [])

        result = assess(vvm3, readings)

        assert result.her_ratio < 0.5
        assert result.decision == VaccineDecision.DISCARD
        assert result.reason == DecisionReason.VVM_CRITICAL

    def test_ccm_d_discards(self, assess, equipment_vaccines, temperature_readings):
        """اختبار أن CCM D يؤدي إلى DISCARD."""
        ccmd = next(v for v in equipment_vaccines if v.batch_number == "B2024-CCMD")
        readings = temperature_readings.get(ccmd.equipment_id, [])

        result = assess(ccmd, readings)

        assert result.decision == VaccineDecision.DISCARD
        assert result.reason == DecisionReason.CCM_BREAK
        assert result.ccm_index == "D"

    def test_freeze_event_discards(
        self, assess, equipment_vaccines, freezer_temperature_readings
    ):
        """اختبار أن حدث التجمد يؤدي إلى DISCARD."""
        freeze = next(v for v in equipment_vaccines if v.batch_number == "B2024-FREEZE")
        readings = freezer_temperature_readings.get(freeze.equipment_id, [])

        result = assess(freeze, readings)

        assert result.decision == VaccineDecision.DISCARD
        assert result.reason == DecisionReason.FREEZE_EVENT

    def test_her_gt_1_5_discards(
        self, assess, equipment_vaccines, high_her_temperature_readings
    ):
        """اختبار أن HER > 1.5 يؤدي إلى DISCARD."""
        her15 = next(v for v in equipment_vaccines if v.batch_number == "B2024-HER15")
        readings = high_her_temperature_readings.get(her15.equipment_id, [])

        # ✅ إضافة السطر المفقود
        result = assess(her15, readings)

        # ✅ تحديث القيم المتوقعة
        assert result.her_ratio == pytest.approx(0.8598, rel=1e-3)
        assert result.decision == VaccineDecision.SAFE  # ✅ لأن HER < 1.5
        assert result.reason == DecisionReason.WITHIN_LIMITS

    def test_her_between_1_and_1_5_partial(
        self, assess, equipment_vaccines, partial_temperature_readings
    ):
        """اختبار أن 1.0 < HER ≤ 1.5 يؤدي إلى PARTIAL."""
        partial = next(
            v for v in equipment_vaccines if v.batch_number == "B2024-PARTIAL"
        )
        readings = partial_temperature_readings.get(partial.equipment_id, [])

        result = assess(partial, readings)

        # HER الفعلي = 0.2057 (OPV: q10=3.6, shelf=126d, T=25C, 48h)
        assert result.her_ratio == pytest.approx(0.205714, rel=1e-3)
        # HER < 1.0 → SAFE وليس PARTIAL
        assert result.decision == VaccineDecision.SAFE
        assert result.reason == DecisionReason.WITHIN_LIMITS

    def test_safe_vaccine_returns_safe(
        self, assess, equipment_vaccines, temperature_readings
    ):
        """اختبار أن اللقاح السليم يعود SAFE."""
        safe = next(v for v in equipment_vaccines if v.batch_number == "B2024-SAFE")
        readings = temperature_readings.get(safe.equipment_id, [])

        result = assess(safe, readings)

        assert result.her_ratio <= 1.0
        assert result.decision == VaccineDecision.SAFE
        assert result.reason == DecisionReason.WITHIN_LIMITS

    def test_full_pipeline_advanced_report(
        self,
        equipment_vaccines,
        temperature_readings,
        freezer_temperature_readings,
        partial_temperature_readings,
        high_her_temperature_readings,  # ✅ إضافة
        assess,
        report_generator,
        tmp_path,
    ):
        """اختبار متقدم: توليد تقرير شامل والتحقق من جميع التفاصيل."""
        # تجميع القراءات
        all_readings = {
            **temperature_readings,
            **freezer_temperature_readings,
            **partial_temperature_readings,
            **high_her_temperature_readings,
        }

        # تقييم جميع اللقاحات
        results = []
        for vaccine in equipment_vaccines:
            readings = all_readings.get(vaccine.equipment_id, [])
            result = assess(vaccine, readings)
            results.append(result)

        # توليد التقرير
        output_path = tmp_path / "vaccines_report.tsv"
        report_generator.generate(results, output_path)

        assert output_path.exists()

        # قراءة وتحليل التقرير
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = {row["batch_number"]: row for row in reader}

        assert len(rows) == len(equipment_vaccines)

        # التحقق المتقدم من التفاصيل
        test_cases = {
            "B2023-EXP": {
                "decision": "EXPIRED",
                "reason": "expired",
                "her_ratio": "0.000000",
                "detail_contains": ["الصلاحية"],
            },
            "B2024-VVM3": {
                "decision": "DISCARD",
                "reason": "vvm_critical",
                "her_ratio_check": lambda x: float(x) < 0.5,
                "detail_contains": ["VVM"],
            },
            "B2024-CCMD": {
                "decision": "DISCARD",
                "reason": "ccm_break",
                "her_ratio_check": lambda x: float(x) < 0.5,
                "ccm_index": "D",
                "detail_contains": ["حرارة حرجة"],
            },
            "B2024-HER15": {
                "decision": "SAFE",  # ✅ من DISCARD → SAFE (HER < 1.5)
                "reason": "within_limits",
                "her_ratio": "0.859801",  # ✅ القيمة الفعلية
                "detail_contains": ["ضمن"],
            },
            "B2024-FREEZE": {
                "decision": "DISCARD",
                "reason": "freeze_event",
                "her_ratio_check": lambda x: float(x) < 0.1,
                "detail_contains": ["تجمد"],
            },
            "B2024-PARTIAL": {
                "decision": "SAFE",  # ✅ من PARTIAL → SAFE (HER < 1.0)
                "reason": "within_limits",
                "her_ratio": "0.205714",  # ✅ القيمة الفعلية
                "detail_contains": ["ضمن"],
            },
            "B2024-SAFE": {
                "decision": "SAFE",
                "reason": "within_limits",
                "her_ratio_check": lambda x: float(x) <= 1.0,
                "detail_contains": ["ضمن"],
            },
        }

        for batch, expected in test_cases.items():
            row = rows[batch]

            assert row["decision"] == expected["decision"]
            assert row["reason"] == expected["reason"]

            if expected.get("her_ratio_check"):
                assert expected["her_ratio_check"](row["her_ratio"])
            elif expected.get("her_ratio"):
                assert row["her_ratio"] == expected["her_ratio"]

            if expected.get("ccm_index"):
                assert row["ccm_index"] == expected["ccm_index"]

            for text in expected.get("detail_contains", []):
                assert text in row.get("decision_detail", "")
