# tests/unit/test_b3_vaccines_report_generator.py
"""
اختبارات وحدة لـ VaccinesReportGenerator — B3.
تختبر توليد تقرير اللقاحات من نتائج التقييم.
"""

from datetime import datetime

from src.application.services.vaccines_report_generator import \
    VaccinesReportGenerator
from src.domain.enums.vaccine_decision import DecisionReason, VaccineDecision
from src.domain.value_objects.vaccine_assessment_result import \
    VaccineAssessmentResult

# ----------------------------------------------------------------------
# دوال مساعدة للاختبارات
# ----------------------------------------------------------------------


def create_test_result(
    equipment_id: str = "EQ-001",
    vaccine_type: str = "OPV",
    batch_number: str = "B2024-001",
    expiry_date: datetime = None,
    decision: VaccineDecision = VaccineDecision.SAFE,
    reason: DecisionReason = DecisionReason.WITHIN_LIMITS,
    her_ratio: float = 0.5,
    ccm_index: str = "A",
    decision_detail: str = "Test assessment",
) -> VaccineAssessmentResult:
    """إنشاء نتيجة تقييم وهمية للاختبار."""
    # لا نغير expiry_date إذا كان None - نتركه كما هو
    return VaccineAssessmentResult(
        equipment_id=equipment_id,
        entry_id=f"ENT-{equipment_id}",
        vaccine_type=vaccine_type,
        batch_number=batch_number,
        expiry_date=expiry_date,
        decision=decision,
        reason=reason,
        her_ratio=her_ratio,
        ccm_index=ccm_index,
        decision_detail=decision_detail,
        evaluated_at=datetime.now(),
    )


# ----------------------------------------------------------------------
# اختبارات VaccinesReportGenerator
# ----------------------------------------------------------------------


class TestVaccinesReportGenerator:
    """اختبارات مولد تقرير اللقاحات."""

    def test_generator_initialization(self):
        """اختبار أن المولد يمكن تهيئته بشكل صحيح."""
        generator = VaccinesReportGenerator()
        assert generator is not None
        assert generator.HEADER == [
            "equipment_id",
            "vaccine_type",
            "batch_number",
            "expiry_date",
            "decision",
            "reason",
            "her_ratio",
            "ccm_index",
            "decision_detail",
        ]

    def test_generate_with_single_result(self, tmp_path):
        """اختبار توليد تقرير بنتيجة واحدة."""
        generator = VaccinesReportGenerator()
        expiry = datetime(2025, 12, 31)

        result = create_test_result(
            equipment_id="EQ-001",
            vaccine_type="OPV",
            batch_number="B2024-001",
            expiry_date=expiry,
            decision=VaccineDecision.SAFE,
            reason=DecisionReason.WITHIN_LIMITS,
            her_ratio=0.5,
            ccm_index="A",
            decision_detail="تقييم آمن",
        )

        output_path = tmp_path / "vaccines_report.tsv"
        result_path = generator.generate([result], output_path)

        assert result_path.exists()
        assert result_path == output_path

        content = result_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(content) == 2  # header + 1 row

        header = content[0].split("\t")
        row = content[1].split("\t")

        assert header[0] == "equipment_id"
        assert header[3] == "expiry_date"

        assert row[0] == "EQ-001"
        assert row[1] == "OPV"
        assert row[2] == "B2024-001"
        assert row[3] == "2025-12-31"
        assert row[4] == "SAFE"  # UPPERCASE للقرار
        assert row[5] == "within_limits"  # lowercase للسبب
        assert float(row[6]) == 0.5
        assert row[7] == "A"
        assert row[8] == "تقييم آمن"

    def test_generate_with_multiple_results(self, tmp_path):
        """اختبار توليد تقرير بنتائج متعددة."""
        generator = VaccinesReportGenerator()

        results = [
            create_test_result(
                equipment_id="EQ-001",
                vaccine_type="OPV",
                batch_number="B2024-001",
                expiry_date=datetime(2025, 12, 31),
                decision=VaccineDecision.SAFE,
                reason=DecisionReason.WITHIN_LIMITS,
                her_ratio=0.5,
                ccm_index="A",
            ),
            create_test_result(
                equipment_id="EQ-001",
                vaccine_type="HepB",
                batch_number="B2024-002",
                expiry_date=datetime(2025, 6, 30),
                decision=VaccineDecision.PARTIAL,
                reason=DecisionReason.PARTIAL_EXPOSURE,
                her_ratio=1.2,
                ccm_index="B",
            ),
            create_test_result(
                equipment_id="EQ-002",
                vaccine_type="BCG",
                batch_number="B2024-003",
                expiry_date=datetime(2024, 12, 31),
                decision=VaccineDecision.DISCARD,
                reason=DecisionReason.VVM_CRITICAL,
                her_ratio=2.5,
                ccm_index="D",
            ),
        ]

        output_path = tmp_path / "vaccines_report.tsv"
        generator.generate(results, output_path)

        content = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(content) == 4  # header + 3 rows

        rows = [line.split("\t") for line in content[1:]]

        # التحقق من القرارات المختلفة (UPPERCASE)
        decisions = [row[4] for row in rows]
        assert "SAFE" in decisions
        assert "PARTIAL" in decisions
        assert "DISCARD" in decisions

        # التحقق من الأسباب (lowercase)
        reasons = [row[5] for row in rows]
        assert "within_limits" in reasons
        assert "partial_exposure" in reasons
        assert "vvm_critical" in reasons

        # التحقق من تواريخ الانتهاء
        assert rows[0][3] == "2025-12-31"
        assert rows[1][3] == "2025-06-30"
        assert rows[2][3] == "2024-12-31"

    def test_generate_with_empty_list(self, tmp_path):
        """اختبار توليد تقرير بقائمة فارغة."""
        generator = VaccinesReportGenerator()
        output_path = tmp_path / "empty_report.tsv"

        result_path = generator.generate([], output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(content) == 1  # header only
        assert "equipment_id" in content[0]
        assert "expiry_date" in content[0]

    def test_generate_with_none_expiry(self, tmp_path):
        """اختبار توليد تقرير عندما يكون expiry_date = None."""
        generator = VaccinesReportGenerator()

        result = create_test_result(
            equipment_id="EQ-001",
            expiry_date=None,
            decision=VaccineDecision.SAFE,
            reason=DecisionReason.WITHIN_LIMITS,
        )

        output_path = tmp_path / "report_no_expiry.tsv"
        generator.generate([result], output_path)

        content = output_path.read_text(encoding="utf-8").strip().split("\n")
        row = content[1].split("\t")

        # expiry_date يجب أن يكون سلسلة فارغة
        assert row[3] == ""

    def test_generate_creates_parent_directory(self, tmp_path):
        """اختبار أن المولد ينشئ المجلدات الوسيطة تلقائياً."""
        generator = VaccinesReportGenerator()
        deep_path = tmp_path / "subdir" / "nested" / "reports" / "vaccines.tsv"

        result = create_test_result(reason=DecisionReason.WITHIN_LIMITS)
        result_path = generator.generate([result], deep_path)

        assert result_path.exists()
        assert deep_path.parent.exists()

    def test_generate_output_format(self, tmp_path):
        """اختبار أن تنسيق الإخراج صحيح (TSV مع فواصل)."""
        generator = VaccinesReportGenerator()
        result = create_test_result(
            her_ratio=0.123456789, reason=DecisionReason.WITHIN_LIMITS
        )

        output_path = tmp_path / "format_test.tsv"
        generator.generate([result], output_path)

        content = output_path.read_text(encoding="utf-8")

        assert "\t" in content

        row = content.strip().split("\n")[1]
        parts = row.split("\t")
        assert len(parts) == 9
        assert parts[6].count(".") == 1
        decimal_part = parts[6].split(".")[1]
        assert len(decimal_part) <= 6

    def test_multiple_equipment_same_expiry(self, tmp_path):
        """اختبار نتائج لأجهزة مختلفة بنفس تاريخ الانتهاء."""
        generator = VaccinesReportGenerator()

        expiry = datetime(2025, 12, 31)
        results = [
            create_test_result(
                equipment_id="EQ-001",
                expiry_date=expiry,
                reason=DecisionReason.WITHIN_LIMITS,
            ),
            create_test_result(
                equipment_id="EQ-002",
                expiry_date=expiry,
                reason=DecisionReason.WITHIN_LIMITS,
            ),
        ]

        output_path = tmp_path / "same_expiry.tsv"
        generator.generate(results, output_path)

        rows = output_path.read_text(encoding="utf-8").strip().split("\n")[1:]
        for row in rows:
            parts = row.split("\t")
            assert parts[3] == "2025-12-31"

    def test_her_ratio_formatting(self, tmp_path):
        """اختبار تنسيق her_ratio بشكل صحيح."""
        generator = VaccinesReportGenerator()

        test_cases = [
            (0.5, "0.500000"),
            (1.0, "1.000000"),
            (1.23456789, "1.234568"),
            (0.0, "0.000000"),
        ]

        for her_value, expected in test_cases:
            result = create_test_result(
                her_ratio=her_value, reason=DecisionReason.WITHIN_LIMITS
            )
            output_path = tmp_path / f"her_{her_value}.tsv"
            generator.generate([result], output_path)

            row = output_path.read_text(encoding="utf-8").strip().split("\n")[1]
            parts = row.split("\t")
            assert parts[6] == expected

    def test_decision_reason_values(self, tmp_path):
        """اختبار أن جميع قيم decision و reason تظهر بشكل صحيح."""
        generator = VaccinesReportGenerator()

        test_data = [
            (VaccineDecision.SAFE, DecisionReason.WITHIN_LIMITS),
            (VaccineDecision.PARTIAL, DecisionReason.PARTIAL_EXPOSURE),
            (VaccineDecision.DISCARD, DecisionReason.HEAT_EXCESS),
            (VaccineDecision.EXPIRED, DecisionReason.EXPIRED),
        ]

        for decision, reason in test_data:
            result = create_test_result(decision=decision, reason=reason)
            output_path = tmp_path / f"decision_{decision.value}.tsv"
            generator.generate([result], output_path)

            row = output_path.read_text(encoding="utf-8").strip().split("\n")[1]
            parts = row.split("\t")
            assert parts[4] == decision.value.upper()  # UPPERCASE
            assert parts[5] == reason.value.lower()  # lowercase
