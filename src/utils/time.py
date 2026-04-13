"""وحدة مساعدة للوقت المشترَك في المشروع."""
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """إرجاع الطابع الزمني الحالي بصيغة ISO 8601 مع UTC."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def format_datetime_ar(dt: datetime) -> str:
    """تنسيق التاريخ والوقت للعربية بصيغة قابلة للقراءة."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")
