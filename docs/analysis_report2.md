=== مسار الملف ===
src/domain/services/exposure_analysis_service.py
===
# src/domain/services/exposure_analysis_service.py
"""
ExposureAnalysisService — محرك التحليل الحراري التراكمي
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from src.domain.entities.temperature_reading import TemperatureReading
    from src.domain.value_objects.vaccine_specification import 
        VaccineSpecification

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
_CCM_UPPER_THRESHOLD: float = 10.0
_CCM_CRITICAL_THRESHOLD: float = 34.0
_CCM_CRITICAL_HOURS: float = 2.0
_FREEZE_THRESHOLD: float = -0.5


class ExposureAnalysisService:
    """
    محرك التحليل الحراري التراكمي.
    Works with both raw log data and FT2 Daily Summary (Split Entry) data.
    """

    def __init__(
        self,
        reference_temp: float = 5.0,
        q10_value: float = 2.0,
        shelf_life_hours: float = 0.0,
    ) -> None:
        self._reference_temp = reference_temp
        self._q10_value = q10_value
        self._shelf_life_hours = shelf_life_hours

    def analyze(
        self,
        readings: List["TemperatureReading"],
        spec: Optional["VaccineSpecification"] = None,
    ) -> Dict:
        if not readings:
            return self._empty_analysis()

        if spec is None:
            from src.domain.value_objects.vaccine_specification import (
                VACCINE_CATALOGUE, VaccineSpecification)

            if self._shelf_life_hours > 0:
                spec = VaccineSpecification(
                    vaccine_type="CUSTOM",
                    q10_factor=self._q10_value,
                    shelf_life_days=self._shelf_life_hours / 24.0,
                    reference_temp_c=self._reference_temp,
                )
            else:
                spec = VACCINE_CATALOGUE["GENERAL"]

        # 1. Circuit Breakers
        circuit_breaker = self._check_circuit_breakers(readings, spec)

        # 2. Basic Stats
        # Note: With Split Entries (Min/Max/Avg), min() and max() correctly reflect absolute extremes.
        temps = [r.value for r in readings]
        max_temp = max(temps)
        min_temp = min(temps)

        # 3. Hours Above Thresholds
        hours_above_10 = self._cumulative_hours_above(readings, _CCM_UPPER_THRESHOLD)
        hours_above_34 = self._cumulative_hours_above(readings, _CCM_CRITICAL_THRESHOLD)

        # 4. CCM Index
        ccm_index = self._calculate_ccm_index(hours_above_10, hours_above_34)

        # 5. Q10 HER
        her_ratio = self._calculate_her_ratio(readings, spec)

        return {
            "her_ratio": her_ratio,
            "ccm_index": ccm_index,
            "has_freeze": min_temp < _FREEZE_THRESHOLD,
            "has_critical_heat": hours_above_34 >= _CCM_CRITICAL_HOURS,
            "max_temp": max_temp,
            "min_temp": min_temp,
            "total_hours_above_10": round(hours_above_10, 2),
            "total_hours_above_34": round(hours_above_34, 4),
            "circuit_breaker": circuit_breaker,
            "data_quality_flags": {"sampling_gap": False},
            "has_ccm_violation": hours_above_10 > 0,
        }

    def _check_circuit_breakers(self, readings, spec) -> Optional[str]:
        if spec.freeze_sensitive:
            min_temp = min(r.value for r in readings)
            if min_temp < _FREEZE_THRESHOLD:
                return "FREEZE_EXCURSION"

        hours_critical = self._cumulative_hours_above(readings, _CCM_CRITICAL_THRESHOLD)
        if hours_critical >= spec.critical_hours:
            return "CRITICAL_HEAT_34C"
        return None

    def _calculate_her_ratio(self, readings, spec) -> float:
        if not readings or spec.shelf_life_hours <= 0:
            return 0.0

        cumulative_degradation_hours = 0.0

        # Prefer explicit duration (supports FT2 Split Entries)
        for reading in readings:
            duration_hours = self._get_duration_hours(reading)
            if duration_hours <= 0:
                continue

            exponent = (reading.value - spec.reference_temp_c) / 10.0
            factor = spec.q10_factor**exponent
            cumulative_degradation_hours += duration_hours * factor

        return cumulative_degradation_hours / spec.shelf_life_hours

    def _calculate_ccm_index(self, hours_above_10, hours_above_34) -> str:
        if hours_above_34 >= _CCM_CRITICAL_HOURS:
            return "D"
        if hours_above_10 >= 336.0:
            return "ABC"
        elif hours_above_10 >= 192.0:
            return "AB"
        elif hours_above_10 >= 72.0:
            return "A"
        else:
            return "0"

    @staticmethod
    def _get_duration_hours(reading) -> float:
        # Check explicit minutes first (FT2 parser output)
        minutes = getattr(reading, "duration_minutes", None)
        if minutes is not None:
            return float(minutes) / 60.0

        hours = getattr(reading, "duration_hours", None)
        if hours is not None:
            return float(hours)

        return 0.0  # Fallback 0 to avoid false assumption

    @staticmethod
    def _cumulative_hours_above(readings, threshold) -> float:
        total_hours = 0.0
        for reading in readings:
            if reading.value > threshold:
                total_hours += ExposureAnalysisService._get_duration_hours(reading)
        return total_hours

    @staticmethod
    def _empty_analysis() -> Dict:
        return {
            "her_ratio": 0.0,
            "ccm_index": "0",
            "has_freeze": False,
            "has_critical_heat": False,
            "max_temp": 0.0,
            "min_temp": 0.0,
            "total_hours_above_10": 0.0,
            "total_hours_above_34": 0.0,
            "circuit_breaker": None,
        }
=== نهاية الملف ===

=== مسار الملف ===
src/domain/services/rules_engine.py
===
# src/domain/services/rules_engine.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.enums.vvm_stage import VVMStage


def calculate_center_stats(center) -> Dict[str, Any]:
    """
    حساب إحصائيات المركز بناءً على القواعد الموحدة.
    يعيد قاموساً يحتوي على المدد الزمنية وحالة الانتهاكات.
    """
    # استخراج الإعدادات (مع قيم افتراضية آمنة)
    temp_ranges = getattr(center, "temperature_ranges", {})
    thresholds = getattr(center, "decision_thresholds", {})

    max_limit = temp_ranges.get("max", 8.0)
    freeze_threshold = thresholds.get("freeze_threshold", 0.0)
    ccm_limit = thresholds.get("ccm_limit", 600)

    entries = getattr(center, "ft2_entries", [])

    if not entries:
        return {
            "freeze_duration": 0,
            "heat_duration": 0,
            "has_freeze": False,
            "has_ccm_violation": False,
            "avg_temp": 0,
            "min_temp": 0,
            "max_temp": 0,
        }

    temperatures = [e.temperature for e in entries if e.temperature is not None]

    # حساب المدد الزمنية بدقة
    freeze_duration = sum(
        e.duration_minutes for e in entries if e.temperature < freeze_threshold
    )
    heat_duration = sum(
        e.duration_minutes for e in entries if e.temperature > max_limit
    )

    return {
        "freeze_duration": freeze_duration,
        "heat_duration": heat_duration,
        "has_freeze": freeze_duration > 0,  # قاعدة عدم التسامح
        "has_ccm_violation": heat_duration > ccm_limit,  # قاعدة التراكم
        "avg_temp": sum(temperatures) / len(temperatures) if temperatures else 0,
        "min_temp": min(temperatures) if temperatures else 0,
        "max_temp": max(temperatures) if temperatures else 0,
    }


# ==========================================
# 🏗️ هيكل القواعد الجديد (Design Pattern)
# ==========================================


class DecisionRule(ABC):
    """
    Abstract Base Class for all safety decision rules.
    """

    @abstractmethod
    def evaluate(self, center: Any, stats: Dict[str, Any]) -> Optional[str]:
        """
        Evaluates the rule against the center's data and stats.

        Args:
            center: The VaccinationCenter or object being evaluated.
            stats: Pre-computed statistics and extra data (e.g., HER).

        Returns:
            Optional[str]: A decision string (e.g., "REJECTED_FREEZE") if the rule
            is triggered, or None if the next rule should be evaluated.
        """
        pass


class ExpiryRule(DecisionRule):
    """قاعدة التحقق من تاريخ الصلاحية (Expiry Date)"""

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        expiry_date_str = getattr(center, "expiry_date", None)
        if not expiry_date_str:
            return None

        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        except ValueError:
            center.decision_reasons.append(
                f"تنسيق تاريخ صلاحية غير صالح: {expiry_date_str}"
            )
            return "REJECTED_EXPIRED"

        if datetime.now().date() > expiry_date:
            center.decision_reasons.append(
                f"لقاح منتهي الصلاحية بتاريخ: {expiry_date_str}"
            )
            return "REJECTED_EXPIRED"

        return None


class FreezeRule(DecisionRule):
    """
    قاعدة التجميد: ذكية وتعتمد على صنف اللقاح (v1.1.0)
    """

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        # استخراج حالة التجميد من اللقاح أو المركز (دعم التوافق مع freeze_sensitive)
        is_freeze_stable = getattr(
            center, "is_freeze_stable", not getattr(center, "freeze_sensitive", True)
        )

        if stats["has_freeze"]:
            if not is_freeze_stable:
                # لقاح حساس للتجميد - رفض فوري أو توصية باختبار الرج
                action = getattr(center, "actions", {}).get(
                    "on_freeze", "تلف فوري محتمل"
                )
                center.decision_reasons.append(
                    f"انتهاك تجميد: {stats['freeze_duration']} دقيقة < 0°C. {action}"
                )
                return "REJECTED_FREEZE"
            else:
                # لقاح مقاوم للتجميد (مثل OPV)
                center.decision_reasons.append(
                    f"تم رصد تجميد ({stats['freeze_duration']} دقيقة) ولكن اللقاح مقاوم للتجميد وفق المكتبة العلمية."
                )
        else:
            center.decision_reasons.append("لم يتم رصد تجميد")
        return None


class HeatCriticalRule(DecisionRule):
    """قاعدة الحرارة الحرجة بناءً على الميزانية الحرارية (v1.1.0)"""

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        critical_limit = getattr(
            center, "critical_temp_limit", stats.get("critical_temp_limit", 10.0)
        )

        if stats["max_temp"] > critical_limit:
            action = getattr(center, "actions", {}).get("on_heat", "حرارة حرجة")
            center.decision_reasons.append(
                f"حرارة حرجة: {stats['max_temp']}°C > {critical_limit}°C. {action}"
            )
            return "REJECTED_HEAT_C"

        if stats["has_ccm_violation"]:
            center.decision_reasons.append(
                f"تجاوز الحد التراكمي (CCM): {stats['heat_duration']} دقيقة"
            )
            return "REJECTED_HEAT_C"

        center.decision_reasons.append(
            "المقاييس الحرارية اللحظية والتراكمية ضمن الحدود"
        )
        return None


class TemperatureWarningRule(DecisionRule):
    """قاعدة التحذير (0-2°C أو 8-10°C)"""

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        if stats["min_temp"] < 2.0 or stats["max_temp"] > 8.0:
            # تسجيل التحذير كسمة إضافية دون تغيير القرار النهائي
            center.decision_reasons.append(
                f"تحذير خروج عن النطاق: ({stats['min_temp']}°C - {stats['max_temp']}°C)"
            )
            center.has_warning = True
            return None
        center.decision_reasons.append("درجات الحرارة ضمن النطاق الآمن (2-8°C)")
        return None


class ThawRule(DecisionRule):
    """
    قاعدة تتبع الذوبان (Thawing Logic) لقاحات mRNA (v1.1.0)
    """

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        if not getattr(center, "ultra_cold_chain_required", False):
            return None

        thaw_start = getattr(center, "thaw_start_time", None)
        max_thaw_days = getattr(center, "thaw_duration_days", 70)

        if thaw_start:
            # حساب الأيام المنقضية منذ الثوب
            if isinstance(thaw_start, str):
                try:
                    thaw_start = datetime.strptime(thaw_start, "%Y-%m-%d")
                except ValueError:
                    return None

            days_since_thaw = (datetime.now() - thaw_start).days

            if days_since_thaw > max_thaw_days:
                center.decision_reasons.append(
                    f"انقضاء صلاحية الثوب: {days_since_thaw} يوم (الحد: {max_thaw_days})"
                )
                return "REJECTED_THAW"
            else:
                remaining = max_thaw_days - days_since_thaw
                center.decision_reasons.append(
                    f"مؤقت الثوب: متبقي {remaining} يوم في الثلاجة."
                )

        return None


class VVMStageRule(DecisionRule):
    """قاعدة تحديد مرحلة VVM بناءً على نسبة التدهور (HER)"""

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        # إذا تم حساب HER مسبقاً في الإحصائيات
        her = stats.get("her", 0.0)

        if her >= 1.0:
            center.vvm_stage = VVMStage.D
            center.decision_reasons.append(
                "VVM المرحلة D: اللقاح منتهي الصلاحية حرارياً"
            )
            return "REJECTED_HEAT_C"
        elif her >= 0.7:
            center.vvm_stage = VVMStage.C
            center.decision_reasons.append(
                "VVM المرحلة C: اقتراب شديد من نهاية الصلاحية"
            )
        elif her >= 0.4:
            center.vvm_stage = VVMStage.B
            center.decision_reasons.append("VVM المرحلة B: تدهور ملحوظ")
        elif her >= 0.1:
            center.vvm_stage = VVMStage.A
            center.decision_reasons.append("VVM المرحلة A: بداية تأثر بالحرارة")
        else:
            center.vvm_stage = VVMStage.NONE

        return None


class DefaultRule(DecisionRule):
    """القاعدة الافتراضية: القبول"""

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        return "ACCEPTED"


class RulesEngine:
    """
    Engine that manages the priority-based execution of Decision Rules.

    Rules are executed in order. The first rule to return a non-None decision
    sets the final outcome for the analysis.

    Priority Table:
    1. ExpiryRule (Critical)
    2. VVMStageRule (Biological/Scientific)
    3. FreezeRule (Zero Tolerance)
    4. HeatCriticalRule (Threshold Violations)
    5. TemperatureWarningRule (Non-decisional monitoring)
    6. DefaultRule (Last resort - Accept)
    """

    def __init__(self):
        # The order in this list defines the precedence.
        self.rules: List[DecisionRule] = [
            ExpiryRule(),  # Priority 0: Biological Expiry
            VVMStageRule(),  # Priority 1: Scientific Degradation (Q10)
            ThawRule(),  # Priority 2: Ultra-Cold Countdown (v1.1.0)
            FreezeRule(),  # Priority 3: Physical Damage (Freeze)
            HeatCriticalRule(),  # Priority 4: Threshold Breaches
            TemperatureWarningRule(),  # Priority 5: Warnings
            DefaultRule(),  # Priority 6: Fallback Accept
        ]

    def run(self, center, stats: Dict[str, Any]):
        for rule in self.rules:
            decision = rule.evaluate(center, stats)
            if decision:
                center.decision = decision
                return


def apply_rules(center, extra_stats: Optional[Dict[str, Any]] = None):
    """واجهة التطبيق المتوافقة مع الكود القديم"""
    # تهيئة قائمة الأسباب للتدقيق (Explainability)
    center.decision_reasons = []

    stats = calculate_center_stats(center)
    if extra_stats:
        stats.update(extra_stats)

    if not getattr(center, "ft2_entries", []):
        center.decision_reasons.append("لا توجد بيانات للجهاز")
        center.decision = "NO_DATA"
        return

    # استخدام المحرك الجديد
    engine = RulesEngine()
    engine.run(center, stats)
=== نهاية الملف ===

=== مسار الملف ===
src/domain/value_objects/vaccine_specification.py
===
# src/domain/value_objects/vaccine_specification.py
"""
VaccineSpecification — مواصفات اللقاح العلمية
المصدر: WHO/IVB/06.10 + WHO/PQS/E06/IN02.1

قيمة ثابتة (frozen) — لا تتغير بعد الإنشاء.
تُستخدم كمدخل لـ Q10HerCalculator و ExposureAnalysisService.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ──────────────────────────────────────────────────────────────
# ثوابت WHO/IVB/06.10 — عتبات CCM الرسمية
# المصدر: WHO/PQS/E06/IN02.1 § 4.2.3
# ──────────────────────────────────────────────────────────────
CCM_WINDOW_A_DAYS_AT_12C: float = 3.0  # نافذة A عند 12°C
CCM_WINDOW_AB_DAYS_AT_12C: float = 8.0  # نافذة A+B عند 12°C
CCM_WINDOW_ABC_DAYS_AT_12C: float = 14.0  # نافذة A+B+C عند 12°C
CCM_CRITICAL_TEMP: float = 34.0  # عتبة النافذة D
CCM_CRITICAL_HOURS: float = 2.0  # ساعتان فوق 34°C = DISCARD

# عتبة HER للقرار (مستنبطة من VVM reaction rates — Table 1 WHO/IVB/06.10)
HER_SAFE_MAX: float = 1.0
HER_PARTIAL_MAX: float = 1.5


@dataclass(frozen=True)
class VaccineSpecification:
    """
    المواصفات العلمية للقاح — مصدر الحقيقة للحسابات الحرارية.

    Attributes:
        vaccine_type:       رمز نوع اللقاح (OPV, HEPB, DTP, ...)
        q10_factor:         معامل Q10 (افتراضي 2.0 وفق Arrhenius)
        shelf_life_days:    العمر الافتراضي للقاح عند درجة المرجع (5°C)
        reference_temp_c:   درجة الحرارة المرجعية للحساب (افتراضي 5.0°C)
        freeze_sensitive:   هل يتلف عند التجمد؟ (لقاحات الألومنيوم)
        vvm_type:           نوع مؤشر VVM (VVM2/7/14/30)
        critical_temp_c:    درجة الخطر الفوري (افتراضي 34.0°C)
        critical_hours:     مدة الخطر الفوري بالساعات (افتراضي 2.0)
        rationale:          مبرر علمي للمواصفات
    """

    vaccine_type: str
    q10_factor: float = 2.0
    shelf_life_days: float = 730.0  # سنتان افتراضياً
    reference_temp_c: float = 5.0
    freeze_sensitive: bool = False
    vvm_type: Optional[str] = None  # VVM2 / VVM7 / VVM14 / VVM30
    critical_temp_c: float = CCM_CRITICAL_TEMP
    critical_hours: float = CCM_CRITICAL_HOURS
    rationale: str = ""
    # ── حقول التوافق الرجعي (legacy) ─────────────────────────
    # محفوظة لمنع كسر الكود القديم — لا تُستخدم في حسابات A1-A4
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    excursion_time_limit: Optional[float] = None
    freeze_range: Optional[tuple] = None
    max_heat_temp: Optional[float] = None
    max_heat_duration_hours: Optional[float] = None
    regulatory_source: Optional[str] = None

    def __post_init__(self) -> None:
        if self.q10_factor <= 0:
            raise ValueError(f"q10_factor must be > 0, got {self.q10_factor}")
        if self.shelf_life_days <= 0:
            raise ValueError(f"shelf_life_days must be > 0, got {self.shelf_life_days}")

    @property
    def shelf_life_hours(self) -> float:
        """العمر الافتراضي بالساعات — مُستخدم في حساب HER ratio."""
        return self.shelf_life_days * 24.0


# ──────────────────────────────────────────────────────────────
# كتالوج اللقاحات الافتراضي — مصدر: WHO/IVB/06.10 Table 9
# ──────────────────────────────────────────────────────────────
VACCINE_CATALOGUE: dict[str, VaccineSpecification] = {
    "OPV": VaccineSpecification(
        vaccine_type="OPV",
        q10_factor=2.0,
        shelf_life_days=225,
        freeze_sensitive=False,
        vvm_type="VVM2",
        rationale="الأكثر حساسية للحرارة — VVM2 ينتهي بعد يومين عند 37°C",
    ),
    "HEPB": VaccineSpecification(
        vaccine_type="HEPB",
        q10_factor=2.0,
        shelf_life_days=1460,  # 4 سنوات
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="مستقر حرارياً — حساس للتجمد (ألومنيوم). VVM30",
    ),
    "DTP": VaccineSpecification(
        vaccine_type="DTP",
        q10_factor=2.0,
        shelf_life_days=548,  # 18 شهراً
        freeze_sensitive=True,
        vvm_type="VVM14",
        rationale="العامل المحدِّد: مكوّن السعال الديكي. حساس للتجمد",
    ),
    "DT": VaccineSpecification(
        vaccine_type="DT",
        q10_factor=2.0,
        shelf_life_days=1095,  # 3 سنوات
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمِّيات ديفتريا وكُزاز — مستقرة. حساسة للتجمد",
    ),
    "TT": VaccineSpecification(
        vaccine_type="TT",
        q10_factor=2.0,
        shelf_life_days=1095,
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمّ الكُزاز — مستقر للغاية. حساس للتجمد",
    ),
    "TD": VaccineSpecification(
        vaccine_type="TD",
        q10_factor=2.0,
        shelf_life_days=1095,
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمِّيات كُزاز وديفتريا (جرعة مخفضة). حساسة للتجمد",
    ),
    "BCG": VaccineSpecification(
        vaccine_type="BCG",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM14",
        rationale="مجفف — يتحمل التجمد. يفقد الفاعلية بالحرارة تدريجياً",
    ),
    "MEASLES": VaccineSpecification(
        vaccine_type="MEASLES",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="مجفف — مستقر نسبياً. يتحمل التجمد",
    ),
    "MMR": VaccineSpecification(
        vaccine_type="MMR",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="مزيج ثلاثي مجفف — المكوّن الأضعف يحدد VVM7",
    ),
    "YF": VaccineSpecification(
        vaccine_type="YF",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="حمى صفراء مجففة — يفقد الفاعلية سريعاً بعد إعادة التركيب",
    ),
    "IPV": VaccineSpecification(
        vaccine_type="IPV",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=True,
        vvm_type="VVM14",
        rationale="شلل الأطفال المعطّل — حساس للتجمد وللحرارة",
    ),
    # افتراضي عام عند عدم معرفة النوع
    "GENERAL": VaccineSpecification(
        vaccine_type="GENERAL",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type=None,
        rationale="مواصفة افتراضية عامة — استخدم عند غياب بيانات النوع",
    ),
}


def get_vaccine_spec(vaccine_type: str) -> VaccineSpecification:
    """
    جلب مواصفات اللقاح من الكتالوج.
    يعود للمواصفة الافتراضية عند غياب النوع.
    """
    normalized = vaccine_type.upper().strip() if vaccine_type else "GENERAL"
    return VACCINE_CATALOGUE.get(normalized, VACCINE_CATALOGUE["GENERAL"])
=== نهاية الملف ===

=== مسار الملف ===
src/domain/calculators/q10_her_calculator.py
===
# src/domain/calculators/q10_her_calculator.py
from __future__ import annotations

import math
from typing import Dict, List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.her_result import HERResult

# ============================================================================
# SCIENTIFIC CONSTANTS — WHO/IVB/06.10
# Q10 = 2.0  للمنتجات البيولوجية العامة (Box 1)
# Tref = 5.0°C  درجة مرجعية اصطلاحية (VVM baseline)
# SHELF_LIFE_HOURS = 48h  حد افتراضي محافظ (قابل للتخصيص لكل لقاح)
# max_gap = 2.0h  حد فجوة القياس — ما فوقه يُقيَّد
# ============================================================================
DEFAULT_Q10 = 2.0
DEFAULT_REFERENCE_TEMP = 5.0
DEFAULT_SHELF_LIFE_HOURS = 48.0  # ✅ اسم موحد مع الاختبار
DEFAULT_MAX_GAP_HOURS = 2.0

# للتوافق الخلفي مع الكود القديم
DEFAULT_shelf_life_hours = DEFAULT_SHELF_LIFE_HOURS


class Q10HerCalculator:
    """
    حساب Heat Exposure Ratio باستخدام نموذج Q10 العلمي.

    المعادلة:
        HER = Σ [ Q10^((T_avg - T_ref)/10) × Δt ]

    حيث T_avg = متوسط درجتي الحرارة للفترة (midpoint — أدق من T_current).

    مقاوم لفجوات القياس (sampling gaps):
        أي Δt > max_gap_hours يُقيَّد إلى max_gap_hours
        ويُسجَّل في data_quality_flags["sampling_gap"].

    المرجع: WHO/IVB/06.10 — Box 1 (Accelerated Degradation Test)
    """

    def __init__(
        self,
        q10_value: float = DEFAULT_Q10,
        reference_temp: float = DEFAULT_REFERENCE_TEMP,
        shelf_life_hours: float = DEFAULT_SHELF_LIFE_HOURS,  # ✅ اسم موحد
        max_gap_hours: float = DEFAULT_MAX_GAP_HOURS,
    ) -> None:
        if q10_value <= 0:
            raise ValueError(f"Q10 يجب أن يكون موجباً: {q10_value}")
        if shelf_life_hours <= 0:
            raise ValueError(f"shelf_life_hours يجب أن يكون موجباً: {shelf_life_hours}")
        if max_gap_hours <= 0:
            raise ValueError(f"max_gap_hours يجب أن يكون موجباً: {max_gap_hours}")

        self._q10 = q10_value
        self._t_ref = reference_temp
        self._shelf_life = shelf_life_hours  # ✅ اسم الخاصية الجديد
        self._max_gap = max_gap_hours

    def calculate_her(self, readings: List[TemperatureReading]) -> HERResult:
        """
        حساب HER من قائمة قراءات درجة الحرارة.
        هذه هي الدالة الأساسية.
        """
        data_quality_flags: Dict[str, bool] = {"sampling_gap": False}

        if len(readings) < 2:
            return HERResult(
                cumulative_degradation_hours=0.0,
                her_ratio=0.0,
                readings_count=len(readings),
                q10_value_used=self._q10,
                reference_temp_used=self._t_ref,
                data_quality_flags=data_quality_flags,
            )

        sorted_readings = sorted(readings, key=lambda r: r.recorded_at)
        her_hours = 0.0

        for i in range(len(sorted_readings) - 1):
            prev = sorted_readings[i]
            curr = sorted_readings[i + 1]

            # المدة الحقيقية بالساعات
            raw_delta_hours = (
                curr.recorded_at - prev.recorded_at
            ).total_seconds() / 3600.0

            if raw_delta_hours <= 0:
                continue

            # تقييد فجوات القياس الكبيرة
            if raw_delta_hours > self._max_gap:
                data_quality_flags["sampling_gap"] = True
                delta_hours = self._max_gap
            else:
                delta_hours = raw_delta_hours

            # متوسط درجة الحرارة للفترة
            avg_temp = (prev.value + curr.value) / 2.0

            # عامل التسريع Q10
            exponent = (avg_temp - self._t_ref) / 10.0
            try:
                factor = math.pow(self._q10, exponent)
            except (ValueError, OverflowError):
                factor = float("inf")

            if math.isinf(factor) or math.isnan(factor):
                her_hours = float("inf")
                break

            her_hours += factor * delta_hours

        # حساب النسبة
        if math.isinf(her_hours):
            her_ratio = float("inf")
        else:
            her_ratio = her_hours / self._shelf_life

        return HERResult(
            cumulative_degradation_hours=her_hours,
            her_ratio=her_ratio,
            readings_count=len(readings),
            q10_value_used=self._q10,
            reference_temp_used=self._t_ref,
            data_quality_flags=data_quality_flags,
        )

    def calculate(self, readings: List[TemperatureReading]) -> HERResult:
        """
        واجهة متوافقة مع الاختبارات - تستدعي calculate_her
        """
        return self.calculate_her(readings)
=== نهاية الملف ===

=== مسار الملف ===
src/domain/calculators/time_weighted_ccm_calculator.py
===
# src/domain/calculators/time_weighted_ccm_calculator.py
from __future__ import annotations

from typing import List

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.ccm_result import CCMResult

# ============================================================================
# DECISION LOCK: TIME UNIT SOURCE OF TRUTH
# 🔒 متوافق مع ccm_calculator.py — الوحدة: دقائق
# ============================================================================
DEFAULT_BASE_TEMP = 8.0  # °C — نهاية نطاق التخزين الموصى به (WHO: 2–8°C)
DEFAULT_THRESHOLD = 1.0  # °C — حد التغيير المعتبر في طريقة Delta


class TimeWeightedCcmCalculator:
    """
    حساب Cold Chain Monitor الموزون زمنياً.

    يُحسن على CCMCalculator الأساسي بإضافة:
    - الوزن الزمني للفترات (فترة أطول = تأثير أكبر)
    - حساب AUC الحراري الدقيق بالتكامل الشبه منحرف
    - حفظ المدة الكلية لتمكين مقارنات مطبّعة

    مستقل تماماً عن HER — لا يشارك حالة، لا يؤثر على نتائجه.

    المرجع: CCM domain model — time-weighted cold chain cumulation
    """

    def __init__(
        self,
        base_temp: float = DEFAULT_BASE_TEMP,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        """
        Args:
            base_temp: درجة الحرارة الأساسية لحساب AUC (افتراضي 8.0°C)
            threshold: حد الفرق الأدنى لاعتبار التغيير في طريقة Delta (افتراضي 1.0°C)
        """
        self._base_temp = base_temp
        self._threshold = threshold

    def calculate(self, readings: List[TemperatureReading]) -> CCMResult:
        """
        حساب CCM من قائمة قراءات درجة الحرارة.

        الخوارزمية:
        طريقة Delta (كلاسيكية):
            - مجموع الفروقات المطلقة ≥ threshold بين القراءات المتتالية
            - مستقلة عن الزمن: تقيس التقلب الحراري

        طريقة AUC (موزونة زمنياً):
            - تكامل شبه منحرف لدرجة الحرارة فوق base_temp
            - الوحدة: degree-minutes
            - تعكس التحميل الحراري الفعلي بدقة أعلى

        Args:
            readings: قائمة قراءات درجة الحرارة (غير مرتبة مقبولة)

        Returns:
            CCMResult: نتيجة الحساب — قيمة نقية بدون حكم
        """
        if len(readings) < 2:
            return CCMResult(
                ccm_delta=0.0,
                ccm_auc=0.0,
                base_temp_used=self._base_temp,
                readings_count=len(readings),
                total_duration_minutes=0.0,
            )

        sorted_readings = sorted(readings, key=lambda r: r.recorded_at)

        ccm_delta = 0.0
        ccm_auc = 0.0
        total_duration_minutes = 0.0
        prev_temp = sorted_readings[0].value

        for i in range(len(sorted_readings) - 1):
            r1 = sorted_readings[i]
            r2 = sorted_readings[i + 1]

            # المدة بالدقائق (TIME_UNIT = minutes — متوافق مع ccm_calculator.py)
            delta_seconds = (r2.recorded_at - r1.recorded_at).total_seconds()
            if delta_seconds <= 0:
                prev_temp = r2.value
                continue

            delta_minutes = delta_seconds / 60.0
            total_duration_minutes += delta_minutes

            # --- طريقة Delta ---
            temp_diff = abs(r2.value - prev_temp)
            if temp_diff >= self._threshold:
                ccm_delta += temp_diff
            prev_temp = r2.value

            # --- طريقة AUC (تكامل شبه منحرف) ---
            temp1 = r1.value
            temp2 = r2.value

            if temp1 > self._base_temp or temp2 > self._base_temp:
                excess1 = max(0.0, temp1 - self._base_temp)
                excess2 = max(0.0, temp2 - self._base_temp)
                avg_excess = (excess1 + excess2) / 2.0
                ccm_auc += avg_excess * delta_minutes

        return CCMResult(
            ccm_delta=ccm_delta,
            ccm_auc=ccm_auc,
            base_temp_used=self._base_temp,
            readings_count=len(readings),
            total_duration_minutes=total_duration_minutes,
        )
=== نهاية الملف ===

=== مسار الملف ===
src/infrastructure/utils/vaccine_library_loader.py
===
# src/infrastructure/utils/vaccine_library_loader.py

import os
from typing import Any, Dict, Optional

import yaml


class VaccineLibraryLoader:
    """
    Loads vaccine definitions from the vaccine_library.yaml file.
    """

    _instance = None
    _library: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VaccineLibraryLoader()
            cls._instance._load_library()
        return cls._instance

    def _load_library(self):
        config_path = "config/vaccine_library.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self._library = data.get("vaccines", {})

    def get_vaccine_data(self, vaccine_id: str) -> Optional[Dict[str, Any]]:
        # Check by id if available
        for key, data in self._library.items():
            if data.get("id") == vaccine_id or key == vaccine_id:
                return data
        return None

    def list_vaccines(self) -> Dict[str, Any]:
        return self._library
=== نهاية الملف ===

=== مسار الملف ===
data/vaccine_catalogue.json
===
{
  "_metadata": {
    "source": "WHO/IVB/06.10 + WHO/PQS/E06/IN02.1",
    "version": "1.0.0",
    "description": "كتالوج اللقاحات المرجعي — ثابت لا يتغير إلا بتحديث WHO",
    "last_updated": "2024-01-01"
  },
  "vaccines": {
    "OPV": {
      "display_name": "لقاح شلل الأطفال الفموي",
      "q10_factor": 2.0,
      "shelf_life_days": 225,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": "VVM2",
      "has_vvm_standard": true,
      "storage_temp_min_c": -25.0,
      "storage_temp_max_c": -15.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "الأكثر حساسية للحرارة — VVM2 ينتهي بعد يومين عند 37°C"
    },
    "HEPB": {
      "display_name": "لقاح التهاب الكبد B",
      "q10_factor": 2.0,
      "shelf_life_days": 1460,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM30",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "مستقر حرارياً — حساس للتجمد (ألومنيوم). VVM30"
    },
    "DTP": {
      "display_name": "لقاح الدفتيريا والكزاز والسعال الديكي",
      "q10_factor": 2.0,
      "shelf_life_days": 548,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM14",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "العامل المحدِّد: مكوّن السعال الديكي. حساس للتجمد"
    },
    "DT": {
      "display_name": "لقاح الدفتيريا والكزاز",
      "q10_factor": 2.0,
      "shelf_life_days": 1095,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM30",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "سُمِّيات ديفتريا وكُزاز — مستقرة. حساسة للتجمد"
    },
    "TT": {
      "display_name": "لقاح الكزاز",
      "q10_factor": 2.0,
      "shelf_life_days": 1095,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM30",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "سُمّ الكُزاز — مستقر للغاية. حساس للتجمد"
    },
    "TD": {
      "display_name": "لقاح الكزاز والدفتيريا (جرعة مخفضة)",
      "q10_factor": 2.0,
      "shelf_life_days": 1095,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM30",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "سُمِّيات كُزاز وديفتريا (جرعة مخفضة). حساسة للتجمد"
    },
    "BCG": {
      "display_name": "لقاح السل",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": "VVM14",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "مجفف — يتحمل التجمد. يفقد الفاعلية بالحرارة تدريجياً"
    },
    "MEASLES": {
      "display_name": "لقاح الحصبة",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": "VVM7",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "مجفف — مستقر نسبياً. يتحمل التجمد"
    },
    "MMR": {
      "display_name": "لقاح الحصبة والنكاف والحصبة الألمانية",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": "VVM7",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "مزيج ثلاثي مجفف — المكوّن الأضعف يحدد VVM7"
    },
    "YF": {
      "display_name": "لقاح الحمى الصفراء",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": "VVM7",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "حمى صفراء مجففة — يفقد الفاعلية سريعاً بعد إعادة التركيب"
    },
    "IPV": {
      "display_name": "لقاح شلل الأطفال المعطّل",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": true,
      "vvm_type": "VVM14",
      "has_vvm_standard": true,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "شلل الأطفال المعطّل — حساس للتجمد وللحرارة"
    },
    "GENERAL": {
      "display_name": "لقاح عام (غير محدد)",
      "q10_factor": 2.0,
      "shelf_life_days": 730,
      "reference_temp_c": 5.0,
      "freeze_sensitive": false,
      "vvm_type": null,
      "has_vvm_standard": false,
      "storage_temp_min_c": 2.0,
      "storage_temp_max_c": 8.0,
      "critical_temp_c": 34.0,
      "critical_hours": 2.0,
      "rationale": "مواصفة افتراضية عامة — استخدم عند غياب بيانات النوع"
    }
  }
}
=== نهاية الملف ===

=== مسار الملف ===
assets/config/system_config.yaml
===
# CCI-FT2 Intelligence System Configuration

system:
  version: "1.0.3"
  environment: "production"
  locale: "ar-SA"

paths:
  fonts_dir: "assets/fonts"
  output_dir: "data/output"
  reports_dir: "data/output/reports"
  logs_dir: "data/logs"

reporting:
  default_theme_color: "#2C3E50"
  accent_color: "#3498DB"
  include_charts: true
  organization_name: "مديرية الصحة العامة"

biological_defaults:
  default_q10: 2.0
  default_ideal_temp: 5.0
  critical_high_threshold: 10.0
  freeze_threshold: 0.0

scenarios:
  vvm_max_her: 1.0
  ccm_max_minutes: 600
=== نهاية الملف ===

=== مسار الملف ===
config/center_profiles.yaml
===
centers:
  TEST_CENTER_01:
    name: "مركز التطعيم التجريبي"
    location: "طرابلس"
    device_ids: ["130600113437"]   # إضافة هذا السطر
    equipment:
      EQ-FRIDGE-01:
        type: "REFRIGERATOR"
        status: "ACTIVE"
        capacity: 120
        note: "الثلاجة الرئيسية — مخصصة لجهاز 130600113437 فقط"

  CENTER_TRIPOLI_01:
    name: "مركز طرابلس الرئيسي"
    location: "طرابلس"
    device_ids: []   # قائمة فارغة إذا لم يكن هناك أجهزة محددة
    equipment:
      EQ-FRIDGE-02:
        type: "REFRIGERATOR"
        status: "ACTIVE"

  CENTER_BENGHAZI_01:
    name: "مركز بنغازي"
    location: "بنغازي"
    device_ids: []
    equipment:
      EQ-FRIDGE-03:
        type: "REFRIGERATOR"
        status: "ACTIVE"
=== نهاية الملف ===

=== مسار الملف ===
scripts/run_ft2_pipeline.py
===
# scripts/run_ft2_pipeline.py
import argparse
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from scripts.create_test_data import create_test_data
from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, TemperatureReading)
from src.application.use_cases.evaluate_cold_chain_safety_use_case import 
    EvaluateColdChainSafetyUseCase
from src.domain.services.rules_engine import (apply_rules,
                                              calculate_center_stats)
from src.infrastructure.adapters.ft2_reader_adapter import FT2ReaderAdapter
from src.infrastructure.logging import get_logger
from src.infrastructure.utils.yaml_loader import load_yaml
from src.presentation.messages.message_map import MessageProvider
from src.presentation.reporting.csv_reporter import generate_centers_report

logger = get_logger(__name__)


# --- Phase 2: Runtime Entity Proxy ---
# نستخدم هذا الكلاس بدلاً من DTO أثناء المعالجة لضمان وجود الإعدادات (temperature_ranges)
# التي يحتاجها محرك القواعد. يتم التحويل إلى DTO فقط عند التقرير.
class RuntimeCenter:
    def __init__(
        self, id, name, device_ids, temperature_ranges=None, decision_thresholds=None
    ):
        self.id = id
        self.name = name
        self.device_ids = device_ids
        self.temperature_ranges = temperature_ranges or {"min": 2.0, "max": 8.0}
        self.decision_thresholds = decision_thresholds or {}
        self.ft2_entries = []

        # حقول النتائج
        self.decision = "UNKNOWN"
        self.vvm_stage = "NONE"
        self.alert_level = None
        self.stability_budget_consumed_pct = 0.0
        self.thaw_remaining_hours = None
        self.category_display = None
        self.decision_reasons = []

    def add_ft2_entry(self, entry):
        self.ft2_entries.append(entry)


def setup_directories():
    """إعداد المجلدات المطلوبة"""
    directories = [
        "data/input_raw",
        "data/input_ft2",
        "data/output",
        "data/reports",
        "config",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug("تم إنشاء/التحقق من المجلد: %s", directory)


def validate_input_directory(input_dir: str) -> bool:
    """
    التحقق من أن مسار الإدخال موجود وهو مجلد.
    إذا كان موجوداً ولكنه ملف، يتم تسجيل خطأ والخروج.
    """
    if not os.path.exists(input_dir):
        logger.error("❌ المسار %s غير موجود.", input_dir)
        return False
    if not os.path.isdir(input_dir):
        logger.error("❌ المسار %s موجود ولكنه ليس مجلداً (ربما هو ملف).", input_dir)
        logger.error("    الرجاء تحديد مجلد يحتوي على ملفات .csv أو .tsv.")
        return False
    return True


def load_centers(config_path: str = "config/center_profiles.yaml") -> List[RuntimeCenter]:
    """تحميل مراكز التطعيم من ملف التكوين"""
    try:
        data = load_yaml(config_path)
        # إذا كان الملف يحتوي على مفتاح 'centers'، نستخرج قائمة المراكز
        if isinstance(data, dict) and "centers" in data:
            centers_dict = data["centers"]
        else:
            centers_dict = data

        # إذا كانت البيانات ليست قاموساً أو قائمة، نخرج خطأ
        if not isinstance(centers_dict, dict):
            logger.error("❌ تنسيق YAML غير صحيح: توقع قاموس (dict) للمراكز")
            return []

        centers = []
        for center_id, profile in centers_dict.items():
            # profile هو قاموس الخصائص
            if not isinstance(profile, dict):
                logger.warning(f"⚠️ الإدخال '{center_id}' ليس قاموساً، يتم تخطيه")
                continue

            # استخراج الحقول
            name = profile.get("name", f"مركز {center_id}")
            device_ids = profile.get("device_ids", [])
            # التأكد من أن device_ids قائمة
            if not isinstance(device_ids, list):
                device_ids = []

            # نطاقات الحرارة
            temp_ranges = profile.get("temperature_ranges")
            # إذا كان هناك "temperature_profiles" (النظام الجديد) نحسب النطاق الأوسع
            if "temperature_profiles" in profile and not temp_ranges:
                temps = profile["temperature_profiles"]
                min_t = min((v["min"] for v in temps.values()), default=2.0)
                max_t = max((v["max"] for v in temps.values()), default=8.0)
                temp_ranges = {"min": min_t, "max": max_t}

            thresholds = profile.get("decision_thresholds")

            # إنشاء كائن RuntimeCenter
            rc = RuntimeCenter(
                id=center_id,
                name=name,
                device_ids=device_ids,
                temperature_ranges=temp_ranges,
                decision_thresholds=thresholds,
            )
            centers.append(rc)

        logger.info(f"تم تحميل {len(centers)} مركز تطعيم (Entities/Profiles)")
        return centers

    except Exception as e:
        logger.critical(f"فشل تحميل التكوين: {e}")
        raise RuntimeError("فشل تحميل إعدادات المراكز") from e


def process_ft2_file_new(
    file_path: str, centers: list, device_map: Dict[str, object] = None
) -> Optional[dict]:
    """
    معالجة ملف FT2 باستخدام النظام الجديد

    Returns:
        dict: نتائج التحليل
    """
    try:
        logger.info("🔍 معالجة الملف (نظام جديد): %s", os.path.basename(file_path))

        # استخدام النظام الجديد عبر الـ Adapter والـ Use Case
        # هذا الدّور الآن يُعهد إلى Use Case التي تتلقى Reader Adapter
        # (التحويل الكامل إلى DTOs يحدث تدريجيًا عبر المappers)
        reader = FT2ReaderAdapter()
        entries = reader.read_all()

        # أثناء المرحلة المرحلية، سنبقي الربط القديم كقيمة احتياطية
        try:
            from src.infrastructure.ft2_reader.services.ft2_linker import 
                FT2Linker

            FT2Linker.link(entries, centers)
        except Exception:
            pass

        # تحليل النتائج لكل مركز
        analysis = {
            "file_path": file_path,
            "parsed_at": datetime.now().isoformat(),
            "entries_count": len(entries),
            "centers_affected": [],
            "analysis": {},
        }

        # تحديد الأجهزة الموجودة في الملف الحالي لتصفية التقرير
        current_file_device_ids = set(entry.device_id for entry in entries)
        affected_centers = set()

        # تحسين الأداء: البحث المباشر باستخدام الخريطة O(1) بدلاً من الحلقات المتداخلة
        if device_map:
            for device_id in current_file_device_ids:
                if device_id in device_map:
                    affected_centers.add(device_map[device_id])
        else:
            # الطريقة القديمة (للاحتياط)
            for center in centers:
                if any(d_id in current_file_device_ids for d_id in center.device_ids):
                    affected_centers.add(center)

        # تجميع النتائج
        for center in affected_centers:
            if center.ft2_entries:  # التأكد من وجود بيانات مرتبطة

                # 1. تطبيق القواعد لتحديث القرار
                apply_rules(center)

                # 2. الحصول على الإحصائيات للتقرير
                stats = calculate_center_stats(center)

                center_analysis = {
                    "center_id": center.id,
                    "center_name": center.name,
                    "entries_count": len(center.ft2_entries),
                    "decision": center.decision,
                    "has_freeze": stats["has_freeze"],
                    "has_ccm_violation": stats["has_ccm_violation"],
                }
                analysis["centers_affected"].append(center_analysis)

        logger.info(
            f"✅ تم معالجة {len(entries)} إدخال لـ {len(analysis['centers_affected'])} مركز"
        )

        return analysis

    except Exception as e:
        logger.error("❌ خطأ في معالجة الملف %s: %s", file_path, e)
        return None


def run_pipeline(
    config_path: str = "config/center_profiles.yaml",
    input_dir: str = "data/input_raw",
    output_dir: str = "data/output",
):
    """تشغيل خط المعالجة الكامل"""

    logger.info(MessageProvider.get("PIPELINE_START"))

    # 1. إعداد المجلدات
    setup_directories()

    # 2. تحميل مراكز التطعيم
    centers = load_centers(config_path)
    
    use_case = EvaluateColdChainSafetyUseCase()

    # تحسين الأداء: إنشاء خريطة البحث السريع (Hash Map) للأجهزة
    # التعقيد: O(1) للبحث بدلاً من O(N)
    device_map = {}
    for center in centers:
        device_ids = (
            getattr(center, "device_ids", [])
            if not isinstance(center, dict)
            else center.get("device_ids", [])
        )
        for device_id in device_ids:
            device_map[device_id] = center

    # 3. التحقق من صحة مجلد الإدخال قبل المعالجة
    if not validate_input_directory(input_dir):
        logger.error("❌ فشل التحقق من مجلد الإدخال. إنهاء التنفيذ.")
        sys.exit(1)

    # 4. الحصول على قائمة الملفات
    ft2_files = []
    ft2_dir = input_dir
    logger.debug("فحص محتويات المجلد: %s", ft2_dir)
    try:
        all_items = os.listdir(ft2_dir)
        logger.debug("الملفات الموجودة: %s", all_items)
        ft2_files = [f for f in all_items if f.endswith((".csv", ".tsv", ".txt"))]
        logger.info(
            "تم العثور على %d ملف(ات) .csv/.tsv/.txt في %s", len(ft2_files), ft2_dir
        )
    except NotADirectoryError:
        logger.error("❌ المسار %s ليس مجلداً (NotADirectoryError).", ft2_dir)
        logger.error("تأكد من أن --input يشير إلى مجلد وليس ملف.")
        logger.debug(traceback.format_exc())
        sys.exit(1)
    except PermissionError as e:
        logger.error("❌ لا توجد صلاحية لقراءة المجلد %s: %s", ft2_dir, e)
        sys.exit(1)
    except Exception as e:
        logger.error("❌ خطأ غير متوقع أثناء قراءة المجلد %s: %s", ft2_dir, e)
        logger.debug(traceback.format_exc())
        sys.exit(1)

    if not ft2_files:
        logger.warning(MessageProvider.get("NO_FILES_TO_PROCESS", path=ft2_dir))

        # اقتراح ذكي للمستخدم
        if not os.listdir(input_dir):
            logger.info(MessageProvider.get("EMPTY_INPUT_DIR_HINT"))
        return

    logger.info(
        MessageProvider.get(
            "FILES_FOUND_TO_PROCESS", count=len(ft2_files), path=ft2_dir
        )
    )

    failed_files = []

    # --- الإصلاح المعماري ---
    # إزالة حالة الاستخدام (Use Case) والعودة إلى منطق التحليل والربط البسيط
    # الذي يتوافق مع بنية البرنامج النصي.
    from src.infrastructure.adapters.berlinger_ft2_reader import 
        BerlingerFt2Reader
    from src.infrastructure.adapters.ft2_reader.services.ft2_linker import 
        FT2Linker

    for ft2_file in ft2_files:
        ft2_path = os.path.join(ft2_dir, ft2_file)
        try:
            # تسجيل مسار الملف ونوعه للتحقق
            logger.debug("محاولة معالجة الملف: %s", ft2_path)
            if not os.path.isfile(ft2_path):
                logger.error("❌ المسار %s ليس ملفاً (تم تخطيه)", ft2_path)
                failed_files.append((ft2_file, "Not a file"))
                continue

            # 1. التحليل (Parse) - دعم FT2 و CSV المعالج
            if '_processed.csv' in ft2_file.lower():
                from src.infrastructure.adapters.processed_csv_reader import ProcessedCsvReader
                reader = ProcessedCsvReader()
                entries = reader.read(ft2_path)
            else:
                reader = BerlingerFt2Reader()
                entries = reader.read(ft2_path)
            
            device_ids_found = set(entry.device_id for entry in entries)
            logger.debug(f"🔍 الأجهزة المستخرجة من الملف: {device_ids_found}")
            
            # 2. الربط (Link) - يدوي للتحكم الكامل
            linked_count = 0
            skipped_count = 0
            
            for entry in entries:
                entry_device_id = getattr(entry, 'device_id', None)
                if not entry_device_id:
                    skipped_count += 1
                    continue
                    
                # البحث عن المركز المناسب
                found_center = False
                for center in centers:
                    if entry_device_id in center.device_ids:
                        center.add_ft2_entry(entry)
                        linked_count += 1
                        found_center = True
                        break
                
                if not found_center:
                    skipped_count += 1
            
            logger.info(f"✅ تم ربط {linked_count} إدخال، تم تخطي {skipped_count}")

        except Exception as e:
            logger.error("❌ خطأ في معالجة الملف %s: %s", ft2_file, e)
            logger.debug(traceback.format_exc())
            failed_files.append((ft2_file, str(e)))

    all_results = []  # للتوافق مع بنية التقرير القديمة
    for center in centers:
        if center.ft2_entries:
            # 1. Prepare Request (Data Only)
            readings = tuple(
                TemperatureReading(
                    value=entry.temperature,   # ← التغيير هنا
                    timestamp=entry.timestamp,
                    device_id=getattr(entry, "device_id", "unknown"),
                )
                for entry in center.ft2_entries
            )

            request = EvaluateColdChainSafetyRequest(
                center_id=center.id,
                center_name=center.name,
                readings=readings,
                temperature_ranges=center.temperature_ranges,
                decision_thresholds=center.decision_thresholds,
            )

            # 2. Execute UseCase (Pure Processing)
            response = use_case.execute(request)
            center.stats = {
                "has_freeze": response.has_freeze,
                "has_ccm_violation": response.has_ccm_violation,
                "her_ratio": getattr(response, "her_ratio", 0.0),
                "ccm_index": getattr(response, "ccm_index", "0"),
            }

            # 3. Update Runtime Object with Results (for reporting compatibility)
            center.decision = response.decision
            center.vvm_stage = response.vvm_stage
            center.alert_level = response.alert_level
            center.stability_budget_consumed_pct = (
                response.stability_budget_consumed_pct
            )
            center.thaw_remaining_hours = response.thaw_remaining_hours
            center.category_display = response.category_display
            center.decision_reasons = list(response.decision_reasons)

            all_results.append(
                {
                    "file_path": "Multiple sources",
                    "centers_affected": [
                        {
                            "center_name": center.name,
                            "entries_count": len(center.ft2_entries),
                        }
                    ],
                }
            )

    # --- Phase 2: Mapping Boundary ---
    # تحويل RuntimeCenter إلى CenterDTO قبل التقرير
    # هذا يضمن أن طبقة التقرير لا تتعامل مع كائنات المجال أو الكائنات المؤقتة
    center_dtos = []
    for c in centers:
        # 🆕 التحقق من البيانات الأساسية
        if not c.id:
            logger.warning("⚠️ مركز بدون ID - سيتم تخطيه: %s", c)
            continue
        
        # 🆕 حساب الإحصائيات الحرارية إذا لم تكن موجودة
        stats = getattr(c, "stats", {}) or {}
        
        if c.ft2_entries and "avg_temp" not in stats:
            temps = []
            for entry in c.ft2_entries:
                # التعامل مع different attribute names
                temp_val = getattr(entry, 'temperature', 
                         getattr(entry, 'value', 
                         getattr(entry, 'temp', None)))
                if temp_val is not None:
                    try:
                        temps.append(float(temp_val))
                    except (ValueError, TypeError):
                        pass
            
            if temps:
                stats = {
                    **stats,
                    "avg_temp": sum(temps) / len(temps),
                    "min_temp": min(temps),
                    "max_temp": max(temps),
                }
                logger.debug("📊 حساب إحصائيات لـ %s: avg=%.2f, min=%.2f, max=%.2f", 
                           c.id, stats["avg_temp"], stats["min_temp"], stats["max_temp"])
        
        # 🆕 إنشاء DTO مع stats في __init__
        dto = CenterDTO(
            id=str(c.id),
            name=str(c.name) if c.name else f"Center-{c.id}",
            device_ids=list(c.device_ids) if c.device_ids else [],
            ft2_entries=list(c.ft2_entries),
            decision=str(c.decision),
            vvm_stage=str(c.vvm_stage),
            alert_level=c.alert_level,
            stability_budget_consumed_pct=float(c.stability_budget_consumed_pct),
            thaw_remaining_hours=c.thaw_remaining_hours,
            category_display=c.category_display,
            decision_reasons=list(c.decision_reasons) if c.decision_reasons else [],
            stats=stats,  # 🆕 تمرير stats هنا مباشرة
        )
        
        center_dtos.append(dto)
        logger.info("✅ تم تحويل المركز: %s - %s (%d إدخال)", 
                   dto.id, dto.name, dto.ft2_entries_count)

    logger.info("📊 إجمالي المراكز المحولة: %d", len(center_dtos))

    # --- Phase 3: Report Generation ---
    # تقرير المراكز
    centers_report_path = os.path.join(output_dir, "centers_report.tsv")
    generate_centers_report(center_dtos, centers_report_path)

    # التقارير التفصيلية
    reports_dir = os.path.join(output_dir, "detailed_reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 6. عرض الملخص
    logger.info("%s", "
" + ("=" * 70))
    logger.info(MessageProvider.get("PIPELINE_SUMMARY_TITLE"))
    logger.info("%s", "=" * 70)
    logger.info(
            MessageProvider.get(
                "FILES_PROCESSED",
                processed_count=len([c for c in center_dtos if c.ft2_entries_count > 0]),
                total_count=len(ft2_files),
            )
        )
    logger.info(MessageProvider.get("FILES_FAILED", failed_count=len(failed_files)))
    logger.info(
            MessageProvider.get("CENTER_REPORT_GENERATED", path=centers_report_path)
        )
    logger.info(
            MessageProvider.get("DETAILED_REPORTS_GENERATED", path=f"{reports_dir}/")
        )

    if failed_files:
            logger.warning(MessageProvider.get("FAILED_FILES_LIST_TITLE"))
            for file, error in failed_files:
                logger.warning("  - %s: %s", file, error)

    logger.info(MessageProvider.get("PIPELINE_COMPLETE", output_dir=output_dir))


def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description=MessageProvider.get("CLI_DESCRIPTION"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s                           # التشغيل الافتراضي
  %(prog)s --config my_config.yaml   # استخدام تكوين مخصص
  %(prog)s --input ./my_data         # مجلد بيانات مخصص
  %(prog)s --verbose                 # عرض تفاصيل أكثر
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="config/center_profiles.yaml",
        help="مسار ملف تكوين المراكز",
    )
    parser.add_argument(
        "--input", "-i", default="data/input_raw", help="مجلد الملفات الخام المدخلة"
    )
    parser.add_argument(
        "--output", "-o", default="data/output", help="مجلد الملفات المخرجة"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="عرض معلومات تفصيلية"
    )
    parser.add_argument(
        "--generate-data",
        action="store_true",
        dest="generate_data",
        help="إنشاء بيانات اختبار في data/input_raw",
    )

    args = parser.parse_args()

    # ضبط مستوى التسجيل
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("وضع التفصيل مفعّل")
        # أيضاً تفعيل DEBUG للمكتبات المستخدمة
        logging.getLogger("src.infrastructure.ft2_reader").setLevel(logging.DEBUG)

    try:
        if getattr(args, "generate_data", False):
            logger.info("🧪 جاري إنشاء بيانات اختبار...")
            create_test_data()

        run_pipeline(
            config_path=args.config, input_dir=args.input, output_dir=args.output
        )
    except Exception as e:
        logger.error(MessageProvider.get("UNEXPECTED_ERROR", error=e))
        logger.debug("التفاصيل الكاملة للخطأ:")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
=== نهاية الملف ===

=== مسار الملف ===
src/domain/entities/temperature_reading.py
===
# src.domain.entities.temperature_reading.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TemperatureReading:
    """
    قراءة درجة حرارة للقاح في وقت محدد.

    Reference: WHO/IVB/06.10 — Temperature monitoring requirements
    """

    vaccine_id: str
    value: float  # درجة الحرارة بالسلسيوس
    recorded_at: datetime
    duration_hours: Optional[float] = None  # مدة القراءة (اختياري)
    device_id: Optional[str] = None  # معرف جهاز المراقبة
    location: Optional[str] = None  # موقع القراءة

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"value يجب أن يكون رقمياً: {self.value}")
        if not isinstance(self.recorded_at, datetime):
            raise ValueError(f"recorded_at يجب أن يكون datetime: {self.recorded_at}")
=== نهاية الملف ===

=== مسار الملف ===
src/application/dtos/analysis_result_dto.py
===
# re-export shim — Phase 5.2 (2026-03-10)
# @DEPRECATED: استخدم src.domain.dtos.analysis_result_dto مباشرة
from src.domain.dtos.analysis_result_dto import (  # noqa: F401
    AnalysisResultDTO, VaccineStatus)

__all__ = ["AnalysisResultDTO", "VaccineStatus"]
=== نهاية الملف ===

=== مسار الملف ===
src/domain/dtos/analysis_result_dto.py
===
# src.domain.dtos/analysis_result_dto.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from src.domain.enums.vvm_stage import VVMStage


class VaccineStatus(Enum):
    SAFE = "SAFE"
    PARTIAL = "PARTIAL"
    DISCARD = "DISCARD"


@dataclass(frozen=True)  # ← immutability enforced
class AnalysisResultDTO:
    vaccine_id: str
    status: VaccineStatus
    her: float
    ccm: float
    vvm_stage: VVMStage = VVMStage.NONE
    alert_level: str = "GREEN"
    category_display: str = ""
    thaw_remaining_hours: Optional[float] = None
    is_thawing: bool = False
    stability_budget_consumed_pct: float = 0.0

    # ⚠️ التغيير الجوهري: جميع الحقول غير قابلة للتغيير
    decision_reasons: Tuple[str, ...] = ()
    audit_log: Tuple[dict, ...] = ()
    recommendations: Tuple[str, ...] = ()
    # ❌ تم إزالة: add_reason(), generate_recommendations()
=== نهاية الملف ===
