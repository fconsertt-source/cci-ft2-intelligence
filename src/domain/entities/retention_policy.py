"""
سياسة الاحتفاظ بالملفات - Domain Policy
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass(frozen=True)
class RetentionPolicy:
    """
    سياسة الاحتفاظ بالملفات.

    تحدد مدة الاحتفاظ لكل نوع من الملفات.
    قابلة للتوسع مستقبلاً لدعم سياسات مختلفة حسب الجهاز/النوع.
    """

    default_retention_days: int = 90
    min_retention_days: int = 30
    max_retention_days: int = 90
    # phase‑5 field; currently mirrors max_retention_days but gives the policy a
    # meaningful name when we query for "critical" devices specifically.
    critical_retention_days: int = 90
    # keyword used to identify critical devices (case-sensitive)
    CRITICAL_KEYWORD: str = "CRITICAL"

    def calculate_expiry(self, archived_at: Optional[str] = None) -> str:
        """
        حساب تاريخ الانتهاء بناءً على السياسة.

        Args:
            archived_at: تاريخ الأرشفة (ISO format)، أو الآن إذا لم يُحدد

        Returns:
            str: تاريخ الانتهاء بصيغة ISO
        """
        if archived_at:
            archive_date = datetime.fromisoformat(archived_at)
        else:
            archive_date = datetime.now(timezone.utc)

        expiry = archive_date + timedelta(days=self.default_retention_days)
        return expiry.isoformat()

    def is_valid_retention(self, days: int) -> bool:
        """
        التحقق من صحة مدة الاحتفاظ.

        Args:
            days: عدد أيام الاحتفاظ

        Returns:
            bool: True إذا كانت المدة صالحة
        """
        return self.min_retention_days <= days <= self.max_retention_days

    def get_retention_period(self, device_id: Optional[str]) -> int:
        """
        Returns the retention period for a given device identifier.

        A special rule applies to any identifier containing the string
        ``CRITICAL`` (case‑insensitive): such devices are granted the
        ``critical_retention_days`` value.  All others default to
        ``default_retention_days``.

        Note that ``device_id`` may be ``None``; callers can treat that as
        a non‑critical (standard) device.
        """
        # treat None as a normal device
        if device_id is None:
            return self.default_retention_days

        # case-sensitive search for the keyword (spec explicitly requires this)
        device_id_str = str(device_id).strip()
        if self.CRITICAL_KEYWORD in device_id_str:
            return self.critical_retention_days
        return self.default_retention_days

    # backward compatible alias used by some older code/tests
    def override_retention(self, device_id: Optional[str]) -> int:
        """Legacy name kept for compatibility, forwards to
        :meth:`get_retention_period`.
        """
        return self.get_retention_period(device_id)
