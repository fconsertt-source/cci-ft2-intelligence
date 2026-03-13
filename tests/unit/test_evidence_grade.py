# tests/unit/test_evidence_grade.py
"""اختبارات وحدة لـ EvidenceGrade"""
import pytest

from src.domain.evidence.evidence_grade import EvidenceGrade


class TestEvidenceGradeNumericValue:
    def test_a_plus_is_100(self):
        assert EvidenceGrade.A_PLUS.numeric_value == 100

    def test_a_is_90(self):
        assert EvidenceGrade.A.numeric_value == 90

    def test_b_is_75(self):
        assert EvidenceGrade.B.numeric_value == 75

    def test_c_is_60(self):
        assert EvidenceGrade.C.numeric_value == 60

    def test_f_is_0(self):
        assert EvidenceGrade.F.numeric_value == 0


class TestEvidenceGradeIsPassing:
    def test_a_plus_passes(self):
        assert EvidenceGrade.A_PLUS.is_passing is True

    def test_a_passes(self):
        assert EvidenceGrade.A.is_passing is True

    def test_b_passes(self):
        assert EvidenceGrade.B.is_passing is True

    def test_c_does_not_pass(self):
        assert EvidenceGrade.C.is_passing is False

    def test_f_does_not_pass(self):
        assert EvidenceGrade.F.is_passing is False


class TestEvidenceGradeRequiresHumanReview:
    def test_b_requires_review(self):
        assert EvidenceGrade.B.requires_human_review is True

    def test_c_requires_review(self):
        assert EvidenceGrade.C.requires_human_review is True

    def test_a_plus_no_review(self):
        assert EvidenceGrade.A_PLUS.requires_human_review is False

    def test_a_no_review(self):
        assert EvidenceGrade.A.requires_human_review is False

    def test_f_no_review(self):
        assert EvidenceGrade.F.requires_human_review is False


class TestEvidenceGradeIsRejected:
    def test_f_is_rejected(self):
        assert EvidenceGrade.F.is_rejected is True

    def test_a_plus_not_rejected(self):
        assert EvidenceGrade.A_PLUS.is_rejected is False

    def test_a_not_rejected(self):
        assert EvidenceGrade.A.is_rejected is False

    def test_b_not_rejected(self):
        assert EvidenceGrade.B.is_rejected is False

    def test_c_not_rejected(self):
        assert EvidenceGrade.C.is_rejected is False
