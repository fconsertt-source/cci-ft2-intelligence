"""
Secure Audit Logger for Security Event Recording.

This module provides tamper-resistant logging for security events,
designed for SIEM integration and compliance auditing.

Security Controls:
- CWE-117: Log Injection Prevention
- CWE-532: Information Exposure Through Log Files
- File permission hardening

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class SecureAuditLogger:
    """
    Secure audit logger for compliance and security monitoring.

    Features:
    - Log injection prevention (CRLF sanitization)
    - Structured logging (JSON-compatible for SIEM)
    - Restrictive file permissions
    - Automatic log rotation
    """

    DANGEROUS_CHARS: str = r"[\r\n\t\x00]"
    MAX_FIELD_LENGTH: int = 1024

    def __init__(
        self,
        log_file: str = "logs/security_audit.log",
        log_level: int = logging.INFO,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
    ) -> None:
        self._log_path = Path(log_file)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("security.audit")
        self._logger.setLevel(log_level)
        self._logger.propagate = False
        self._logger.handlers.clear()

        handler = RotatingFileHandler(
            self._log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setLevel(log_level)

        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        try:
            os.chmod(self._log_path, 0o600)
        except OSError as e:
            self._logger.warning(f"Could not set log file permissions: {e}")

        self._logger.info("SecureAuditLogger initialized")

    def _sanitize(self, value: Any) -> str:
        if value is None:
            return "null"
        str_value = str(value)
        if len(str_value) > self.MAX_FIELD_LENGTH:
            str_value = str_value[: self.MAX_FIELD_LENGTH] + "...[truncated]"
        sanitized = re.sub(self.DANGEROUS_CHARS, "", str_value)
        return sanitized

    def log_event(
        self,
        action: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()

        log_entry = {
            "timestamp": timestamp,
            "action": self._sanitize(action),
            "user_id": self._sanitize(user_id),
            "success": success,
            "details": {},
        }

        if details:
            for key, value in details.items():
                log_entry["details"][self._sanitize(key)] = self._sanitize(value)

        level = logging.INFO if success else logging.WARNING
        self._logger.log(level, json.dumps(log_entry))

    def log_auth_failure(
        self, user_id: str, reason: str, ip_address: Optional[str] = None
    ) -> None:
        details = {"reason": reason}
        if ip_address:
            details["ip_address"] = ip_address
        self.log_event("AUTH_FAILURE", user_id, details, success=False)

    def log_auth_success(self, user_id: str, method: str = "token") -> None:
        self.log_event("AUTH_SUCCESS", user_id, {"method": method}, success=True)

    def log_access_denied(
        self, user_id: str, action: str, resource: Optional[str] = None
    ) -> None:
        details = {"action": action}
        if resource:
            details["resource"] = resource
        self.log_event("ACCESS_DENIED", user_id, details, success=False)

    def log_report_generated(
        self, user_id: str, report_path: str, report_type: str
    ) -> None:
        report_filename = Path(report_path).name
        self.log_event(
            "REPORT_GENERATED",
            user_id,
            {"filename": report_filename, "type": report_type},
            success=True,
        )
