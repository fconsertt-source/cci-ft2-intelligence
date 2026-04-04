"""
Domain Validator: قواعد سلامة سلسلة التبريد.
نقية تماماً — لا Pydantic، لا مكتبات خارجية.
"""
from dataclasses import dataclass
from typing import Tuple, List

@dataclass(frozen=True)
class FT2ValidationRules:
    """
    قواعد التحقق المستمدة من معايير WHO لسلسلة التبريد.
    كل رقم هنا له مصدر علمي/تنظيمي.
    """
    TEMP_MIN_CELSIUS: float = -30.0   # حد التجميد المطلق
    TEMP_MAX_CELSIUS: float = +50.0   # حد الحرارة المطلق
    TEMP_FREEZE_THRESHOLD: float = 0.0  # حد انتهاك التجميد
    TEMP_HEAT_THRESHOLD: float = 8.0    # حد انتهاك الحرارة
    DURATION_MAX_MINUTES: int = 1440    # 24 ساعة كحد يومي
    DURATION_MIN_MINUTES: int = 0

class FT2EntryValidator:
    """
    Validator نقي في Domain.
    يتحقق من صحة كل إدخال قبل قبوله في النظام.
    """
    RULES = FT2ValidationRules()

    @classmethod
    def validate_temperature(
        cls, value: float
    ) -> Tuple[bool, str, str]:
        """
        يُعيد: (is_valid, reason_ar, reason_en)
        """
        if not cls.RULES.TEMP_MIN_CELSIUS <= value <= cls.RULES.TEMP_MAX_CELSIUS:
            return False, (
                f"درجة الحرارة {value}°C خارج النطاق الفيزيائي "
                f"({cls.RULES.TEMP_MIN_CELSIUS} إلى {cls.RULES.TEMP_MAX_CELSIUS})"
            ), (
                f"Temperature {value}°C outside physical range "
                f"({cls.RULES.TEMP_MIN_CELSIUS} to {cls.RULES.TEMP_MAX_CELSIUS})"
            )
        return True, "", ""

    @classmethod
    def validate_duration(
        cls, minutes: int
    ) -> Tuple[bool, str, str]:
        if not (cls.RULES.DURATION_MIN_MINUTES
                <= minutes
                <= cls.RULES.DURATION_MAX_MINUTES):
            return False, (
                f"المدة {minutes} دقيقة خارج النطاق المسموح"
            ), (
                f"Duration {minutes} minutes outside allowed range"
            )
        return True, "", ""

    @classmethod
    def validate_entry(cls, entry: dict) -> List[Tuple[str, str]]:
        """
        يتحقق من إدخال كامل.
        يُعيد قائمة بالأخطاء (فارغة إذا كان صحيحاً).
        """
        errors = []

        temp = entry.get("temperature")
        if temp is None:
            errors.append(("درجة الحرارة مفقودة", "Temperature missing"))
        else:
            try:
                valid, ar, en = cls.validate_temperature(float(temp))
                if not valid:
                    errors.append((ar, en))
            except (TypeError, ValueError):
                errors.append((
                    f"درجة الحرارة غير رقمية: {temp}",
                    f"Non-numeric temperature: {temp}"
                ))

        duration = entry.get("duration_minutes")
        if duration is not None:
            try:
                valid, ar, en = cls.validate_duration(int(duration))
                if not valid:
                    errors.append((ar, en))
            except (TypeError, ValueError):
                errors.append((f"المدة غير صحيحة: {duration}", f"Invalid duration: {duration}"))

        return errors
