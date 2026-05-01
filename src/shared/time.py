from datetime import datetime, timezone

def utc_now_iso(timespec: str = 'seconds') -> str:
    """
    إرجاع الوقت الحالي بصيغة ISO مع Zulu indicator (Z) للدلالة على UTC.
    يضمن التناسق في تمثيل الأوقات عبر النظام.
    """
    # datetime.now(timezone.utc) يعطي كائن datetime مع معلومات المنطقة الزمنية UTC
    return datetime.now(timezone.utc).isoformat(timespec=timespec).replace('+00:00', 'Z')