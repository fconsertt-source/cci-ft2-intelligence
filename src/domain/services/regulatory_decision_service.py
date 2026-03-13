# src/domain/services/regulatory_decision_service.py
from __future__ import annotations

from typing import Literal

from src.domain.value_objects.vaccine_specification import VaccineSpecification

# الأنواع المسموح بها — ثابتة بعقد معماري
DecisionOutcome = Literal["SAFE", "PARTIAL", "DISCARD"]

# ============================================================================
# DECISION LOCK — لا تغيير بدون تحديث contracts + tests
# ============================================================================
# SAFE    ← درجة الحرارة ومدة التعرض ضمن الحدود التنظيمية
# PARTIAL ← تجاوز max_temp لكن المدة لم تبلغ الحد الأقصى بعد
# DISCARD ← تجميد مؤذٍ، أو تجاوز max_heat_temp، أو استنفاد مدة الحد المسموح
# ============================================================================


class RegulatoryDecisionService:
    """
    يُصدر قرارات بناءً على الحدود التنظيمية فقط.

    القواعد مرتّبة حسب الأولوية:
    1. التجميد المؤذي (Freeze check)  ← DISCARD فوري، قاعدة مطلقة
    2. التجميد المسموح (Frozen storage) ← SAFE إذا كان اللقاح يُحفظ مجمداً
    3. تجاوز max_heat_temp (الحد الأقصى المطلق) ← DISCARD فوري
    4. فحص المدة عند تجاوز max_temp (الحد العادي)
       - مدة ≥ max_heat_duration_hours ← DISCARD
       - مدة < max_heat_duration_hours ← PARTIAL
    5. ضمن النطاق الطبيعي ← SAFE

    مبدأ التصميم:
    - لا نماذج احتمالية
    - لا تقديرات علمية (هذه مهمة ThermalDegradationEstimator)
    - كل قرار مرتبط بمصدر تنظيمي واضح (WHO/IVB/06.10)
    """

    def evaluate(
        self,
        temperature: float,
        duration_minutes: float,
        spec: VaccineSpecification,
    ) -> DecisionOutcome:
        """
        Args:
            temperature: درجة الحرارة الفعلية بالسيلزيوس
            duration_minutes: مدة التعرض بالدقائق
            spec: مواصفات اللقاح التنظيمية

        Returns:
            "SAFE" | "PARTIAL" | "DISCARD"
        """

        # ── 1. فحص التجميد المؤذي ────────────────────────────────────────────
        # اللقاحات الحساسة للتجميد: أي تجميد = DISCARD (قاعدة مطلقة WHO)
        # المصدر: WHO/IVB/06.10 § 3 — "Freezing does not affect non-potency
        #          parameters... but freezing does affect immunogenicity"
        if spec.freeze_sensitive and temperature <= 0.0:
            return "DISCARD"

        # ── 2. فحص التجميد المسموح (اللقاحات المُجمَّدة) ─────────────────────
        # بعض اللقاحات تُحفظ في نطاق تجميد محدد (OPV: -15 إلى -25°C)
        if not spec.freeze_sensitive and spec.freeze_range is not None:
            freeze_min, freeze_max = spec.freeze_range
            if freeze_min <= temperature <= freeze_max:
                return "SAFE"
            # تجميد خارج النطاق المحدد = غير متوقع = DISCARD
            if temperature <= 0.0:
                return "DISCARD"

        # اللقاح غير حساس ولا يملك freeze_range معرّف — تجميد غير متوقع
        if not spec.freeze_sensitive and spec.freeze_range is None and temperature <= 0.0:
            return "DISCARD"

        # ── 3. تجاوز الحد الأقصى المطلق (max_heat_temp) ─────────────────────
        # هذا الحد لا تسمح به أي مدة مهما قصرت
        max_heat_temp = (
            spec.max_heat_temp if spec.max_heat_temp is not None else spec.max_temp
        )
        if temperature > max_heat_temp:
            return "DISCARD"

        # ── 4. فحص تجاوز max_temp (النطاق العادي) ───────────────────────────
        if temperature > spec.max_temp:
            duration_hours = duration_minutes / 60.0
            max_allowed_hours = spec.max_heat_duration_hours or 0.0

            if duration_hours >= max_allowed_hours:
                return "DISCARD"

            # تجاوز الحد لكن المدة لم تبلغ الحد الأقصى بعد
            return "PARTIAL"

        # ── 5. ضمن النطاق الطبيعي ────────────────────────────────────────────
        return "SAFE"