"""
Secure Global Error Handler v2.2.

Prevents information leakage through error messages and stack traces.
Integrated with SecureAuditLogger for comprehensive security logging.

Security Controls:
- CWE-209: Information Exposure Through Error Message
- CWE-215: Information Exposure Through Debug Information
- CWE-117: Log Injection Prevention (via SecureAuditLogger)

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, Optional

from src.application.security.secure_logger import SecureAuditLogger


class SecureErrorHandler:
    """
    Global error handler for production security.

    Features:
    - Hides stack traces from end users in production
    - Logs full details internally via SecureAuditLogger
    - Prevents information leakage
    - Generates safe error codes for tracking
    """

    SAFE_MESSAGES: Dict[str, str] = {
        "PermissionError": "You are not authorized to perform this action",
        "ValueError": "Invalid input provided",
        "IOError": "File operation failed",
        "TimeoutError": "Operation timed out",
        "default": "An unexpected error occurred",
    }

    def __init__(
        self,
        environment: Optional[str] = None,
        audit_logger: Optional[SecureAuditLogger] = None,
    ) -> None:
        self._environment = environment or os.getenv("CCIF_ENVIRONMENT", "development")
        self._is_production = self._environment.lower() == "production"
        self._audit_logger = audit_logger or SecureAuditLogger()

    def handle(
        self,
        exception: Exception,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._log_internal(exception, context)
        safe_message = user_message or self._get_safe_message(exception)
        error_code = self._get_error_code(exception)

        if self._is_production:
            return {"success": False, "message": safe_message, "error_code": error_code}
        else:
            return {
                "success": False,
                "message": safe_message,
                "error_code": error_code,
                "error_type": type(exception).__name__,
                "details": str(exception),
            }

    def _log_internal(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        user_id = context.get("user_id", "system") if context else "system"
        action = context.get("action", "unknown") if context else "unknown"

        self._audit_logger.log_event(
            action="ERROR_OCCURRED",
            user_id=user_id,
            details={
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "action": action,
                "traceback_available": True,
            },
            success=False,
        )

        internal_logger = logging.getLogger("security.errors")
        internal_logger.error(
            f"Internal error: {type(exception).__name__}: {exception}", exc_info=True
        )

    def _get_safe_message(self, exception: Exception) -> str:
        exc_type = type(exception).__name__
        return self.SAFE_MESSAGES.get(exc_type, self.SAFE_MESSAGES["default"])

    def _get_error_code(self, exception: Exception) -> str:
        error_str = f"{type(exception).__name__}:{str(exception)}"
        hash_value = hashlib.sha256(error_str.encode()).hexdigest()[:8].upper()
        return f"ERR_{hash_value}"


_global_handler: Optional[SecureErrorHandler] = None


def get_error_handler() -> SecureErrorHandler:
    global _global_handler
    if _global_handler is None:
        env = os.getenv("CCIF_ENVIRONMENT", "production")
        _global_handler = SecureErrorHandler(environment=env)
    return _global_handler
