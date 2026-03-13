from datetime import datetime, timezone

def utc_now_iso(timespec: str = 'seconds') -> str:
    """
    إرجاع الوقت الحالي بصيغة ISO 8601 مع Zulu indicator (UTC).
    
    Args:
        timespec: دقة الوقت ('auto', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds')
    
    Returns:
        str: الوقت بصيغة YYYY-MM-DDTHH:MM:SS.ssssssZ
    """
    return datetime.now(timezone.utc).isoformat(timespec=timespec).replace('+00:00', 'Z')
