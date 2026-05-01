# src/domain/services/rules_engine.py
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.domain.enums.vvm_stage import VVMStage

# محاولة استيراد logger بشكل آمن (قد يكون غير متاح في بعض السياقات)
import logging
_logger = logging.getLogger(__name__)


def _extract_temperature(entry):
    """محاولة موحدة لاستخراج قيمة الحرارة من entry (object أو dict)."""
    try:
        if hasattr(entry, "temperature"):
            val = getattr(entry, "temperature")
            if val is not None and val != "":
                return float(val)
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract temperature attribute: %s", e)

    try:
        if hasattr(entry, "temp"):
            val = getattr(entry, "temp")
            if val is not None and val != "":
                return float(val)
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract temp attribute: %s", e)

    try:
        if isinstance(entry, dict):
            for key in ("temperature", "temp", "temp_c", "value", "reading"):
                if key in entry and entry[key] not in (None, ""):
                    return float(entry[key])
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract temperature from dict: %s", e)

    return None


def _extract_duration_minutes(entry):
    """محاولة موحدة لاستخراج مدة القراءة بالدقائق من entry."""
    try:
        if hasattr(entry, "duration_minutes"):
            val = getattr(entry, "duration_minutes")
            if val is not None and val != "":
                return float(val)
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract duration_minutes attribute: %s", e)

    try:
        if hasattr(entry, "duration"):
            val = getattr(entry, "duration")
            if val is not None and val != "":
                return float(val)
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract duration attribute: %s", e)

    try:
        if isinstance(entry, dict):
            for key in ("duration_minutes", "duration", "minutes"):
                if key in entry and entry[key] not in (None, ""):
                    return float(entry[key])
    except (ValueError, TypeError) as e:
        _logger.debug("Failed to extract duration from dict: %s", e)

    return 0.0


def calculate_center_stats(center) -> Dict[str, Any]:
    """
    حساب إحصائيات المركز وإرجاع مفاتيح متوافقة مع مُولّد التقرير.
    """
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
            "has_heat_duration_breach": False,
            "avg_temperature": 0.0,
            "min_temperature": 0.0,
            "max_temperature": 0.0,
        }

    temperatures = []
    for e in entries:
        t = _extract_temperature(e)
        if t is not None:
            temperatures.append(t)

    freeze_duration = 0.0
    heat_duration = 0.0
    for e in entries:
        t = _extract_temperature(e)
        duration = _extract_duration_minutes(e)
        if t is None:
            continue
        if t < freeze_threshold:
            freeze_duration += duration
        if t > max_limit:
            heat_duration += duration

    has_freeze = freeze_duration > 0
    has_heat_duration_breach = heat_duration > ccm_limit

    avg_temperature = sum(temperatures) / len(temperatures) if temperatures else 0.0
    min_temperature = min(temperatures) if temperatures else 0.0
    max_temperature = max(temperatures) if temperatures else 0.0

    try:
        _logger.debug(
            "DEBUG stats for center %s: temps=%s avg=%s min=%s max=%s freeze_dur=%s heat_dur=%s",
            getattr(center, "id", "unknown"),
            temperatures,
            avg_temperature,
            min_temperature,
            max_temperature,
            freeze_duration,
            heat_duration,
        )
    except Exception as e:
        _logger.warning("Failed to log debug stats: %s", e)

    return {
        "freeze_duration": freeze_duration,
        "heat_duration": heat_duration,
        "has_freeze": has_freeze,
        "has_heat_duration_breach": has_heat_duration_breach,
        "avg_temperature": avg_temperature,
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
    }


# ==========================================
# 🏗️ هيكل القواعد الجديد (Design Pattern)
# ==========================================


class DecisionRule(ABC):
    @abstractmethod
    def evaluate(self, center: Any, stats: Dict[str, Any]) -> Optional[str]:
        pass


class ExpiryRule(DecisionRule):
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

        if datetime.now(timezone.utc).date() > expiry_date:
            center.decision_reasons.append(
                f"لقاح منتهي الصلاحية بتاريخ: {expiry_date_str}"
            )
            return "REJECTED_EXPIRED"

        return None


class FreezeRule(DecisionRule):
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        freeze_sensitive = getattr(center, "freeze_sensitive", True)
        is_freeze_stable = getattr(center, "is_freeze_stable", not freeze_sensitive)

        if stats.get("has_freeze", False):
            if freeze_sensitive and not is_freeze_stable:
                # لقاح حساس → رفض
                action = getattr(center, "actions", {}).get(
                    "on_freeze", "تلف فوري محتمل"
                )
                center.decision_reasons.append(
                    f"انتهاك تجميد: {stats.get('freeze_duration', 0)} دقيقة < 0°C. {action}"
                )
                return "REJECTED_FREEZE"
            else:
                # لقاح مقاوم للتجميد → تحذير فقط
                center.decision_reasons.append(
                    f"تم رصد تجميد ({stats.get('freeze_duration', 0)} دقيقة) ولكن اللقاح مقاوم للتجميد."
                )
                # لا نرفض، لكن نضع تحذير
                center.has_warning = True
        else:
            center.decision_reasons.append("لم يتم رصد تجميد")
        return None


class HeatCriticalRule(DecisionRule):
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        # محاولة الحصول على max_temp من stats أولاً، وإلا حسابه من الإدخالات
        max_temp = stats.get("max_temp")
        if max_temp is None and hasattr(center, "ft2_entries"):
            temps = []
            for e in center.ft2_entries:
                t = _extract_temperature(e)
                if t is not None:
                    temps.append(t)
            if temps:
                max_temp = max(temps)
        if max_temp is None:
            return None

        critical_limit = getattr(center, "critical_temp_limit", stats.get("critical_temp_limit", 10.0))
        if max_temp > critical_limit:
            action = getattr(center, "actions", {}).get("on_heat", "حرارة حرجة")
            center.decision_reasons.append(
                f"حرارة حرجة: {max_temp:.1f}°C > {critical_limit}°C. {action}"
            )
            return "REJECTED_HEAT_C"

        if stats.get("has_heat_duration_breach", False):
            center.decision_reasons.append(
                f"تجاوز الحد التراكمي (CCM): {stats.get('heat_duration', 0)} دقيقة"
            )
            return "REJECTED_HEAT_C"

        center.decision_reasons.append(
            "المقاييس الحرارية اللحظية والتراكمية ضمن الحدود"
        )
        return None


class TemperatureWarningRule(DecisionRule):
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        min_temp = stats.get("min_temp")
        max_temp = stats.get("max_temp")

        # fallback إذا لم تكن موجودة في stats
        if min_temp is None or max_temp is None:
            if hasattr(center, "ft2_entries") and center.ft2_entries:
                temps = [_extract_temperature(e) for e in center.ft2_entries if _extract_temperature(e) is not None]
                if temps:
                    min_temp = min(temps)
                    max_temp = max(temps)

        if min_temp is None or max_temp is None:
            return None

        if min_temp < 2.0 or max_temp > 8.0:
            center.decision_reasons.append(
                f"تحذير خروج عن النطاق: ({min_temp:.1f}°C - {max_temp:.1f}°C)"
            )
            center.has_warning = True
            return None   # لا نرفض، فقط تحذير

        center.decision_reasons.append("درجات الحرارة ضمن النطاق الآمن (2-8°C)")
        return None


class ThawRule(DecisionRule):
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        if not getattr(center, "ultra_cold_chain_required", False):
            return None

        thaw_start = getattr(center, "thaw_start_time", None)
        max_thaw_days = getattr(center, "thaw_duration_days", 70)

        if thaw_start:
            if isinstance(thaw_start, str):
                try:
                    thaw_start = datetime.strptime(thaw_start, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    return None

            days_since_thaw = (datetime.now(timezone.utc) - thaw_start).days

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
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        # دعم كلا المفتاحين (her_ratio من الخدمة الجديدة + her من القديم)
        her = stats.get("her_ratio", stats.get("her", 0.0))

        flexible_vvm_allowed = getattr(center, "flexible_vvm_allowed", False) or stats.get(
            "flexible_vvm_allowed", False
        )

        if her >= 1.0:
            center.vvm_stage = VVMStage.D
            center.decision_reasons.append(
                f"VVM المرحلة D: HER ratio = {her:.3f} ≥ 1.0 → منتهي حرارياً"
            )
            return "REJECTED_HEAT_C"
        elif her >= 0.7:
            center.vvm_stage = VVMStage.C
            if (
                flexible_vvm_allowed
                and getattr(center, "vaccine_type", "").upper() == "OPV"
            ):
                center.decision_reasons.append(
                    "Fast Chain Flexible VVM policy applied for OPV campaigns"
                )
            else:
                center.decision_reasons.append(f"VVM المرحلة C: HER = {her:.3f}")
        elif her >= 0.4:
            center.vvm_stage = VVMStage.B
            center.decision_reasons.append(f"VVM المرحلة B: HER = {her:.3f}")
        elif her >= 0.1:
            center.vvm_stage = VVMStage.A
            center.decision_reasons.append(f"VVM المرحلة A: HER = {her:.3f}")
        else:
            center.vvm_stage = VVMStage.NONE

        return None


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
    def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
        return "ACCEPTED"


class RulesEngine:
    def __init__(self, enable_heat_duration: bool = False):
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
    center.decision_reasons = []
    if not hasattr(center, 'has_warning'):
        center.has_warning = False

    stats = calculate_center_stats(center)
    if extra_stats:
        stats.update(extra_stats)

    if not getattr(center, "ft2_entries", []):
        center.decision_reasons.append("لا توجد بيانات للجهاز")
        center.decision = "NO_DATA"
        return

    engine = RulesEngine(enable_heat_duration=enable_heat_duration)
    engine.run(center, stats)