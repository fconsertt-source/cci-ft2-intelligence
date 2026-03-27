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

class HeatDurationRule(DecisionRule):
    """قاعدة مدة الحرارة فوق max_temp باستخدام max_heat_duration_hours"""

    def __init__(self, enable_heat_duration: bool = False):
        self._enable = enable_heat_duration

class HeatDurationRule(DecisionRule):
    def __init__(self, enable_heat_duration: bool = False):
        self._enable = enable_heat_duration

    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        if not self._enable:
            return None

        vaccine_spec = getattr(center, 'vaccine_spec', None)
        if not vaccine_spec:
            return None

        max_allowed_hours = getattr(vaccine_spec, 'max_heat_duration_hours', None)
        if max_allowed_hours is None:
            return None

        heat_duration_minutes = stats.get('heat_duration', 0)
        duration_hours = heat_duration_minutes / 60.0

        if duration_hours > max_allowed_hours:
            center.decision_reasons.append(
                f"تجاوز المدة المسموحة: {duration_hours:.1f} ساعة > {max_allowed_hours} ساعة"
            )
            return "REJECTED_HEAT_C"
        elif duration_hours > 0:
            center.decision_reasons.append(
                f"تجاوز درجة الحرارة الموصى بها لمدة {duration_hours:.1f} ساعة (مسموح {max_allowed_hours} ساعة)"
            )
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

class RulesEngine:
    def __init__(self, enable_heat_duration: bool = False):
        # ترتيب القواعد يحدد الأولوية
        self.rules: List[DecisionRule] = [
            ExpiryRule(),
            VVMStageRule(),
            ThawRule(),
            FreezeRule(),
            HeatCriticalRule(),
            HeatDurationRule(enable_heat_duration=enable_heat_duration),
            TemperatureWarningRule(),
            DefaultRule(),
        ]

    def run(self, center, stats: Dict[str, Any]):
        for rule in self.rules:
            decision = rule.evaluate(center, stats)
            if decision:
                center.decision = decision
                return


def apply_rules(center, extra_stats: Optional[Dict[str, Any]] = None, enable_heat_duration: bool = False):
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
    engine = RulesEngine(enable_heat_duration=enable_heat_duration)
    engine.run(center, stats)
