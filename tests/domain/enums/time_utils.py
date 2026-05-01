from datetime import datetime, timezone

def utc_now_iso(timespec: str = 'seconds') -> str:
    """
    Returns the current UTC time in ISO 8601 format with a 'Z' suffix.
    This replaces deprecated datetime.utcnow().isoformat().
    """
    return datetime.now(timezone.utc).isoformat(timespec=timespec).replace('+00:00', 'Z')

def utc_now_datetime() -> datetime:
    """Returns the current UTC datetime object."""
    return datetime.now(timezone.utc)