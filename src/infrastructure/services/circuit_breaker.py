"""
Circuit Breaker: يمنع ملفاً تالفاً من إيقاف خط المعالجة كله.
"""
import logging
from pathlib import Path
from typing import Callable, TypeVar, Optional

logger = logging.getLogger(__name__)
T = TypeVar("T")

class FileCircuitBreaker:
    """
    بعد MAX_ERRORS أخطاء في ملف واحد:
    - ينقله للـ Quarantine
    - يستمر مع الملف التالي (Graceful Degradation)
    - لا ينهار خط المعالجة
    """
    MAX_ERRORS = 5

    def __init__(self, quarantine_handler):
        self._quarantine = quarantine_handler
        self._error_counts: dict = {}

    def execute_with_protection(
        self,
        file_path: Path,
        operation: Callable[[], T],
        fallback: Optional[T] = None
    ) -> Optional[T]:
        """
        ينفّذ العملية مع حماية Circuit Breaker.
        عند الفشل: يسجّل الخطأ ويعيد fallback.
        """
        file_key = str(file_path)
        errors = self._error_counts.get(file_key, 0)

        if errors >= self.MAX_ERRORS:
            logger.error(
                "Circuit Open للملف %s — تجاوز %d أخطاء / "
                "Circuit open for %s — exceeded %d errors",
                file_path.name, self.MAX_ERRORS,
                file_path.name, self.MAX_ERRORS
            )
            self._quarantine.quarantine_file(
                file_path,
                reason_ar=f"تجاوز الحد الأقصى للأخطاء: {errors}",
                reason_en=f"Exceeded max errors: {errors}"
            )
            return fallback

        try:
            result = operation()
            # نجاح — أعد العدّاد
            self._error_counts.pop(file_key, None)
            return result

        except Exception as e:
            self._error_counts[file_key] = errors + 1
            logger.warning(
                "خطأ في %s (محاولة %d/%d): %s / "
                "Error in %s (attempt %d/%d): %s",
                file_path.name, errors + 1, self.MAX_ERRORS, str(e),
                file_path.name, errors + 1, self.MAX_ERRORS, str(e)
            )
            # Note: We return None to indicate failure within this file's processing
            return fallback