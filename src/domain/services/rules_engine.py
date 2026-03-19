from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List, Optional

from src.domain.enums.vvm_stage import VVMStage
from src.domain.services.rules_engine_stats import RulesEngineStats


def _coerce_stats(stats) -> RulesEngineStats:
    """Convert plain dict → RulesEngineStats (test compatibility)."""
    if isinstance(stats, dict):
        return RulesEngineStats.from_dict(stats)
    return stats


# =========================================================
# 🧠 Aggregation Layer (Typed)
# =========================================================
def calculate_center_stats(center) -> RulesEngineStats:
    """
    Build typed statistics for RulesEngine.
    """

    temp_ranges = getattr(center, "temperature_ranges", {})
    thresholds = getattr(center, "decision_thresholds", {})

    max_limit = temp_ranges.get("max", 8.0)
    freeze_threshold = thresholds.get("freeze_threshold", 0.0)
    ccm_limit = thresholds.get("ccm_limit", 600)

    entries = getattr(center, "ft2_entries", [])

    if not entries:
        return RulesEngineStats()

    temperatures = [e.temperature for e in entries if e.temperature is not None]

    freeze_duration = sum(
        e.duration_minutes for e in entries if e.temperature < freeze_threshold
    )

    heat_duration = sum(
        e.duration_minutes for e in entries if e.temperature > max_limit
    )

    has_ccm_violation = heat_duration > ccm_limit

    return RulesEngineStats(
        max_temp=max(temperatures) if temperatures else 0.0,
        min_temp=min(temperatures) if temperatures else 0.0,
        avg_temp=sum(temperatures) / len(temperatures) if temperatures else 0.0,
        freeze_duration=freeze_duration,
        heat_duration=heat_duration,
        has_freeze=freeze_duration > 0,
        has_ccm_violation=has_ccm_violation,
        her=0.0,  # سيتم ربطه لاحقًا مع Q10
    )


# =========================================================
# 🏗️ Decision Rules (Typed بالكامل)
# =========================================================
class DecisionRule(ABC):
    @abstractmethod
    def evaluate(self, center: Any, stats: RulesEngineStats) -> Optional[str]:
        pass


# ---------------------------------------------------------
class ExpiryRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
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


# ---------------------------------------------------------
class FreezeRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        stats = _coerce_stats(stats)
        is_freeze_stable = getattr(
            center,
            "is_freeze_stable",
            not getattr(center, "freeze_sensitive", True),
        )

        if stats.has_freeze:
            if not is_freeze_stable:
                action = getattr(center, "actions", {}).get(
                    "on_freeze", "تلف فوري محتمل"
                )

                center.decision_reasons.append(
                    f"انتهاك تجميد: {stats.freeze_duration} دقيقة < 0°C. {action}"
                )

                return "REJECTED_FREEZE"
            else:
                center.decision_reasons.append(
                    f"تم رصد تجميد ({stats.freeze_duration} دقيقة) ولكن اللقاح مقاوم للتجميد."
                )
        else:
            center.decision_reasons.append("لم يتم رصد تجميد")

        return None


# ---------------------------------------------------------
class HeatCriticalRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        stats = _coerce_stats(stats)
        critical_limit = getattr(center, "critical_temp_limit", 10.0)

        if stats.max_temp > critical_limit:
            action = getattr(center, "actions", {}).get("on_heat", "حرارة حرجة")

            center.decision_reasons.append(
                f"حرارة حرجة: {stats.max_temp}°C > {critical_limit}°C. {action}"
            )

            return "REJECTED_HEAT_C"

        if stats.has_ccm_violation:
            center.decision_reasons.append(
                f"تجاوز الحد التراكمي (CCM): {stats.heat_duration} دقيقة"
            )
            return "REJECTED_HEAT_C"

        center.decision_reasons.append(
            "المقاييس الحرارية اللحظية والتراكمية ضمن الحدود"
        )

        return None


class CCMIndexRule(DecisionRule):
    """
    قاعدة CCM حسب النطاقات العلمية المعتمدة من WHO

    النطاقات:
    - D: تجاوز 34°C لأكثر من ساعتين → REJECT فوري
    - ABC: تجاوز 10°C لأكثر من 336 ساعة → REJECT
    - AB: تجاوز 10°C لأكثر من 192 ساعة → WARNING
    - A: تجاوز 10°C لأكثر من 72 ساعة → WARNING
    - 0: آمن

    الأولوية: 5.5 (بعد HeatCriticalRule وقبل TemperatureWarningRule)
    """

    priority = 5.5

    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        # الحصول على ccm_index من center (محسوب في exposure_analysis_service)
        ccm_index = getattr(center, "ccm_index", None)

        if not ccm_index:
            return None  # لا يوجد معلومات CCM

        # القرار حسب النطاق
        if ccm_index == "D":
            center.decision_reasons.append(
                "CCM Index D: تجاوز درجة الحرارة الحرجة (34°C) لأكثر من ساعتين"
            )
            return "REJECTED_HEAT_C"

        if ccm_index == "ABC":
            center.decision_reasons.append(
                "CCM Index ABC: تجاوز 10°C لأكثر من 336 ساعة (14 يوم)"
            )
            return "REJECTED_HEAT_C"

        if ccm_index in ["AB", "A"]:
            center.decision_reasons.append(
                f"CCM Index {ccm_index}: تجاوز 10°C لفترة طويلة"
            )
            return "WARNING"  # تحذير وليس رفض

        # ccm_index == "0" → آمن
        return None


# ---------------------------------------------------------
class TemperatureWarningRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        stats = _coerce_stats(stats)
        if stats.min_temp < 2.0 or stats.max_temp > 8.0:
            center.decision_reasons.append(
                f"تحذير خروج عن النطاق: ({stats.min_temp}°C - {stats.max_temp}°C)"
            )
            center.has_warning = True
            return None

        center.decision_reasons.append("درجات الحرارة ضمن النطاق الآمن (2-8°C)")
        return None


# ---------------------------------------------------------
class ThawRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        if not getattr(center, "ultra_cold_chain_required", False):
            return None

        thaw_start = getattr(center, "thaw_start_time", None)
        max_thaw_days = getattr(center, "thaw_duration_days", 70)

        if thaw_start:
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

            remaining = max_thaw_days - days_since_thaw
            center.decision_reasons.append(
                f"مؤقت الثوب: متبقي {remaining} يوم في الثلاجة."
            )

        return None


# ---------------------------------------------------------
class VVMStageRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        her = stats.her

        if her >= 1.0:
            center.vvm_stage = VVMStage.D
            center.decision_reasons.append("VVM المرحلة D")
            return "REJECTED_HEAT_C"

        elif her >= 0.7:
            center.vvm_stage = VVMStage.C
            center.decision_reasons.append("VVM المرحلة C")
        elif her >= 0.4:
            center.vvm_stage = VVMStage.B
            center.decision_reasons.append("VVM المرحلة B")
        elif her >= 0.1:
            center.vvm_stage = VVMStage.A
            center.decision_reasons.append("VVM المرحلة A")
        else:
            center.vvm_stage = VVMStage.NONE

        return None


# ---------------------------------------------------------
class DefaultRule(DecisionRule):
    def evaluate(self, center, stats: RulesEngineStats) -> Optional[str]:
        return "ACCEPTED"


# =========================================================
# ⚙️ Rules Engine
# =========================================================
class RulesEngine:
    def __init__(self):
        self.rules: List[DecisionRule] = [
            ExpiryRule(),
            VVMStageRule(),
            ThawRule(),
            FreezeRule(),
            HeatCriticalRule(),
            TemperatureWarningRule(),
            DefaultRule(),
        ]

    def run(self, center, stats: RulesEngineStats):
        stats = _coerce_stats(stats)
        for rule in self.rules:
            decision = rule.evaluate(center, stats)
            if decision:
                center.decision = decision
                return


# =========================================================
# 🚀 Public API
# =========================================================
def apply_rules(center, extra_stats=None):
    center.decision_reasons = []

    stats = calculate_center_stats(center)

    if extra_stats:
        if isinstance(extra_stats, dict):
            stats = RulesEngineStats.from_dict({**stats.to_dict(), **extra_stats})
        else:
            stats = extra_stats

    if not getattr(center, "ft2_entries", []):
        center.decision_reasons.append("لا توجد بيانات للجهاز")
        center.decision = "NO_DATA"
        return

    engine = RulesEngine()
    engine.run(center, stats)
