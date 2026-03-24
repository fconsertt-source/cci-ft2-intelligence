"""
Secure Report Generation Use Case v2.2.

Security Controls:
- CWE-22: Path Traversal Prevention
- CWE-287: Authentication/Authorization
- CWE-78: OS Command Injection Prevention
- Audit Logging

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.application.ports.i_authorizer import IAuthorizer
from src.application.ports.i_reporter import IReporter
from src.application.security.secure_logger import SecureAuditLogger

logger = logging.getLogger("security.audit")


class GenerateReportUseCase:
    """Secure use case for generating reports."""

    def __init__(
        self,
        generator: IReporter,
        authorizer: Optional[IAuthorizer] = None,
        audit_logger: Optional[SecureAuditLogger] = None,
        output_dir: str = "reports",
    ) -> None:
        self._generator = generator
        self._authorizer = authorizer
        self._audit_logger = audit_logger or SecureAuditLogger()

        self._output_dir = Path(output_dir).resolve()
        self._output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"GenerateReportUseCase initialized with output_dir: {self._output_dir}"
        )

    def execute(
        self, request: Any, user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        user_context = user_context or {}
        user_id = user_context.get("user_id", "system")
        action = "generate_report"

        # STEP 1: AUTHORIZATION (Optional for Offline Mode)
        if self._authorizer:
            if not self._authorizer.authorize(action, user_context):
                self._audit_logger.log_access_denied(user_id, action)
                logger.warning(f"Unauthorized report generation attempt by {user_id}")
                raise PermissionError(f"User '{user_id}' is not authorized to {action}")
            self._audit_logger.log_auth_success(user_id)

        # STEP 2: INPUT VALIDATION
        try:
            self._validate_request(request)
        except ValueError as e:
            self._audit_logger.log_event(
                "INVALID_REQUEST", user_id, {"error": str(e)}, success=False
            )
            raise

        # STEP 3: SECURE PATH GENERATION
        output_path = self._generate_secure_path(user_id, request)

        # Verify path is within allowed directory
        try:
            output_path.resolve().relative_to(self._output_dir)
        except ValueError:
            self._audit_logger.log_event(
                "PATH_TRAVERSAL_ATTEMPT",
                user_id,
                {"path": str(output_path)},
                success=False,
            )
            raise ValueError("Invalid output path detected")

        # STEP 4: REPORT GENERATION
        try:
            self._generator.generate(request, output_path)
        except Exception as e:
            self._audit_logger.log_event(
                "GENERATION_FAILURE", user_id, {"error": str(e)}, success=False
            )
            raise

        # STEP 5: AUDIT LOGGING
        self._audit_logger.log_report_generated(
            user_id,
            str(output_path),
            getattr(request, "report_type", "unknown") if request else "unknown",
        )

        logger.info(f"Report generated successfully: {output_path}")
        return str(output_path)

    def _validate_request(self, request: Any) -> None:
        if request is None:
            raise ValueError("Request cannot be None")

    def _generate_secure_path(self, user_id: str, request: Any) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_user_id = user_id.replace("/", "_").replace("\\", "_")[:32]
        report_type = getattr(request, "report_type", "report") if request else "report"
        safe_report_type = str(report_type).replace("/", "_")[:32]
        filename = f"{safe_report_type}_{safe_user_id}_{timestamp}.pdf"
        return self._output_dir / filename
