#!/usr/bin/env python3
"""اختبارات JudgmentEngine"""

import pytest

from src.domain.enums.vaccine_decision import VaccineDecision
from src.domain.services.judgment_engine import JudgmentEngine


class TestJudgmentEngine:
    """اختبارات محرك الحكم"""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine(vaccine_data_version="2.0.3")

    def test_safe_decision(self, engine):
        """اختبار قرار SAFE"""
        result = engine.judge(
            decision=VaccineDecision.SAFE,
            decision_reason="جميع القراءات ضمن النطاق",
            her_ratio=0.1,
        )

        assert result.risk_level == "SAFE"
        assert result.risk_icon == "🟢"
        assert result.confidence >= 0.9
        assert result.requires_human_review is False
        assert "سليم" in result.narrative

    def test_partial_decision(self, engine):
        """اختبار قرار PARTIAL"""
        result = engine.judge(
            decision=VaccineDecision.PARTIAL,
            decision_reason="تجاوز بسيط لدرجة الحرارة",
            her_ratio=0.7,
        )

        assert result.risk_level in ["MEDIUM", "HIGH"]
        assert result.risk_icon in ["🟡", "🔴"]
        assert "يُستخدم بحذر" in result.narrative

    def test_discard_decision(self, engine):
        """اختبار قرار DISCARD"""
        result = engine.judge(
            decision=VaccineDecision.DISCARD,
            decision_reason="تجاوز الحد المسموح",
            her_ratio=1.2,
        )

        assert result.risk_level == "HIGH"
        assert result.risk_icon == "🔴"
        assert result.requires_human_review is True
        assert "إتلاف" in result.narrative

    def test_critical_heat(self, engine):
        """اختبار حرارة حرجة"""
        result = engine.judge(
            decision=VaccineDecision.DISCARD,
            decision_reason="حرارة حرجة",
            has_critical_heat=True,
            her_ratio=1.5,
        )

        assert result.risk_level == "CRITICAL"
        assert result.risk_icon == "🚨"
        assert result.confidence < 0.85

    def test_freeze_detected(self, engine):
        """اختبار تجمد"""
        result = engine.judge(
            decision=VaccineDecision.DISCARD,
            decision_reason="تجمد",
            freeze_detected=True,
        )

        assert result.requires_human_review is True
        assert result.confidence < 0.9
        assert "تجمد" in result.narrative

    def test_high_her_requires_review(self, engine):
        """HER عالية تحتاج مراجعة"""
        result = engine.judge(
            decision=VaccineDecision.PARTIAL,
            decision_reason="HER مرتفع",
            her_ratio=0.95,
        )

        assert result.requires_human_review is True
        assert result.her_percentage == 95.0

    def test_low_confidence(self, engine):
        """ثقة منخفضة تحتاج مراجعة"""
        result = engine.judge(
            decision=VaccineDecision.SAFE,
            decision_reason="بيانات محدودة",
            confidence=0.7,
        )

        assert result.requires_human_review is True
        assert result.confidence == 0.7

    def test_ccm_index_d(self, engine):
        """CCM Index D يحتاج مراجعة"""
        result = engine.judge(
            decision=VaccineDecision.PARTIAL,
            decision_reason="CCM مرتفع",
            ccm_index="D",
        )

        assert result.requires_human_review is True
        assert result.ccm_index == "D"

    def test_recommendations_for_discard(self, engine):
        """توصيات للإتلاف"""
        result = engine.judge(
            decision=VaccineDecision.DISCARD,
            decision_reason="إتلاف",
            freeze_detected=True,
        )

        assert "إتلاف" in result.recommendations[0]
        assert "تجمد" in " ".join(result.recommendations)

    def test_recommendations_for_partial(self, engine):
        """توصيات للاستخدام بحذر"""
        result = engine.judge(
            decision=VaccineDecision.PARTIAL,
            decision_reason="استخدام بحذر",
        )

        assert any("اختبار" in r for r in result.recommendations)

    def test_vaccine_data_version(self, engine):
        """إصدار بيانات اللقاح"""
        result = engine.judge(
            decision=VaccineDecision.SAFE,
            decision_reason="آمن",
        )

        assert result.vaccine_data_version == "2.0.3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
