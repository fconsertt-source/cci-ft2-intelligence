#!/usr/bin/env python3
"""Judgment Engine — طبقة الحكم البشري فوق RulesEngine"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

from src.domain.enums.vaccine_decision import VaccineDecision


class RiskLevel(Enum):
    """مستويات المخاطرة"""

    SAFE = "safe"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class JudgmentOutput:
    """مخرجات الحكم البشري"""

    risk_level: str  # SAFE / MEDIUM / HIGH / CRITICAL
    risk_icon: str  # 🟢 / 🟡 / 🔴 / 🚨
    narrative: str  # وصف عربي ديناميكي
    recommendations: List[str]
    her_percentage: float
    freeze_detected: bool
    requires_human_review: bool
    confidence: float  # 0.0–1.0
    vaccine_data_version: str
    decision_reason: str
    ccm_index: str = "0"


class JudgmentEngine:
    """
    محرك الحكم البشري - يشرح قرار RulesEngine بلغة مفهومة

    المبدأ:
    - RulesEngine = Authority (القرار القانوني الصارم)
    - JudgmentEngine = Explanation (الشرح البشري المفهوم)
    """

    def __init__(self, vaccine_data_version: str = "2.0.3"):
        self.vaccine_data_version = vaccine_data_version

    def judge(
        self,
        decision: VaccineDecision,
        decision_reason: str,
        her_ratio: float = 0.0,
        ccm_index: str = "0",
        freeze_detected: bool = False,
        has_critical_heat: bool = False,
        vaccine_spec: Any = None,
        confidence: Optional[float] = None,
    ) -> JudgmentOutput:
        """
        إصدار حكم بشري بناءً على قرار RulesEngine

        Args:
            decision: قرار RulesEngine (SAFE/PARTIAL/DISCARD)
            decision_reason: سبب القرار من RulesEngine
            her_ratio: نسبة HER المحسوبة (0.0-1.0+)
            ccm_index: مؤشر CCM (A, AB, ABC, D, 0)
            freeze_detected: هل تم اكتشاف تجمد؟
            has_critical_heat: هل تم اكتشاف حرارة حرجة؟
            vaccine_spec: مواصفات اللقاح
            confidence: درجة الثقة (محسوبة تلقائياً إذا لم تُعط)

        Returns:
            JudgmentOutput: الحكم البشري مع التوصيات
        """

        her_percentage = her_ratio * 100

        # حساب درجة الثقة
        if confidence is None:
            confidence = self._calculate_confidence(
                her_ratio, freeze_detected, has_critical_heat, ccm_index
            )

        # تحديد مستوى المخاطرة
        risk_level, risk_icon = self._determine_risk_level(
            decision, her_ratio, freeze_detected, has_critical_heat, ccm_index
        )

        # إنشاء السرد التوضيحي
        narrative = self._generate_narrative(
            decision, decision_reason, her_percentage, freeze_detected, ccm_index
        )

        # تحديد ما إذا كان يحتاج مراجعة بشرية
        requires_human_review = self._needs_human_review(
            decision, her_ratio, freeze_detected, confidence, ccm_index
        )

        # إنشاء التوصيات
        recommendations = self._generate_recommendations(
            decision, freeze_detected, has_critical_heat, ccm_index
        )

        return JudgmentOutput(
            risk_level=risk_level,
            risk_icon=risk_icon,
            narrative=narrative,
            recommendations=recommendations,
            her_percentage=her_percentage,
            freeze_detected=freeze_detected,
            requires_human_review=requires_human_review,
            confidence=confidence,
            vaccine_data_version=self.vaccine_data_version,
            decision_reason=decision_reason,
            ccm_index=ccm_index,
        )

    def _calculate_confidence(
        self,
        her_ratio: float,
        freeze_detected: bool,
        has_critical_heat: bool,
        ccm_index: str,
    ) -> float:
        """حساب درجة الثقة (0.0-1.0)"""
        confidence = 1.0

        # نقص الثقة عند وجود تجمد
        if freeze_detected:
            confidence -= 0.15

        # نقص الثقة عند وجود حرارة حرجة
        if has_critical_heat:
            confidence -= 0.2

        # نقص الثقة عند ارتفاع HER
        if her_ratio > 1.0:
            confidence -= 0.1
        elif her_ratio > 1.5:
            confidence -= 0.2

        # نقص الثقة عند CCM مرتفع
        if ccm_index == "D":
            confidence -= 0.15
        elif ccm_index in ["ABC", "AB"]:
            confidence -= 0.1

        return max(0.5, min(1.0, confidence))  # بين 0.5 و 1.0

    def _determine_risk_level(
        self,
        decision: VaccineDecision,
        her_ratio: float,
        freeze_detected: bool,
        has_critical_heat: bool,
        ccm_index: str,
    ) -> tuple:
        """تحديد مستوى المخاطرة والأيقونة"""
        if decision == VaccineDecision.DISCARD:
            if has_critical_heat or ccm_index == "D":
                return ("CRITICAL", "🚨")
            return ("HIGH", "🔴")

        if decision == VaccineDecision.PARTIAL:
            if her_ratio > 0.8:
                return ("HIGH", "🔴")
            return ("MEDIUM", "🟡")

        # SAFE
        if freeze_detected or her_ratio > 0.5:
            return ("MEDIUM", "🟡")
        return ("SAFE", "🟢")

    def _generate_narrative(
        self,
        decision: VaccineDecision,
        decision_reason: str,
        her_percentage: float,
        freeze_detected: bool,
        ccm_index: str,
    ) -> str:
        """إنشاء سرد توضيحي بالعربية"""

        base = f"القرار: {decision.value}. "

        if decision == VaccineDecision.DISCARD:
            base += "يجب إتلاف اللقاح. "
            if freeze_detected:
                base += "تم اكتشاف تجمد. "
            if her_percentage > 100:
                base += f"استهلك {her_percentage:.0f}% من الميزانية الحرارية. "
        elif decision == VaccineDecision.PARTIAL:
            base += "يُستخدم بحذر مع تحليل إضافي. "
            if her_percentage > 50:
                base += f"استهلك {her_percentage:.0f}% من الميزانية الحرارية. "
        else:
            base += "اللقاح سليم وآمن للاستخدام. "

        if ccm_index != "0":
            base += f"مؤشر CCM: {ccm_index}. "

        base += decision_reason
        return base

    def _needs_human_review(
        self,
        decision: VaccineDecision,
        her_ratio: float,
        freeze_detected: bool,
        confidence: float,
        ccm_index: str,
    ) -> bool:
        """تحديد ما إذا كان القرار يحتاج مراجعة بشرية"""
        # أي رفض يحتاج مراجعة
        if decision == VaccineDecision.DISCARD:
            return True

        # قريب من الحد الحرج (HER ≥ 0.9)
        if her_ratio >= 0.9:
            return True

        # تجمد دائماً يحتاج مراجعة
        if freeze_detected:
            return True

        # ثقة منخفضة في البيانات
        if confidence < 0.75:
            return True

        # CCM حرج
        if ccm_index in ["D", "ABC"]:
            return True

        return False

    def _generate_recommendations(
        self,
        decision: VaccineDecision,
        freeze_detected: bool,
        has_critical_heat: bool,
        ccm_index: str,
    ) -> List[str]:
        """إنشاء توصيات عملية"""
        recommendations = []

        if decision == VaccineDecision.DISCARD:
            recommendations.append("🚫 إتلاف اللقاح فوراً")
            recommendations.append("📝 توثيق الحادثة في سجل التبريد")

            if freeze_detected:
                recommendations.append("❄️ مراجعة جهاز التبريد والتأكد من عدم وجود تجمد")
            if has_critical_heat:
                recommendations.append("🔥 مراجعة إنذارات الحرارة العالية في الجهاز")

        elif decision == VaccineDecision.PARTIAL:
            recommendations.append("🔍 إجراء اختبار إضافي للقاح")
            recommendations.append("📊 متابعة درجة الحرارة عن كثب")

            if ccm_index in ["A", "AB"]:
                recommendations.append("⏰ تقليل وقت فتح الثلاجة")

        else:  # SAFE
            recommendations.append("✅ استخدام اللقاح بشكل طبيعي")
            recommendations.append("📈 متابعة الروتين اليومي للتبريد")

        return recommendations
