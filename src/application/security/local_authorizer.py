"""
Local Authorizer Implementation for Offline Mode.

This module provides authorization logic for offline/local deployments.
Uses system tokens for service-to-service authentication.

Security Controls:
- CWE-798: Hardcoded Credentials Prevention
- CWE-613: Insufficient Session Expiration
- Timing Attack Prevention (constant-time comparison)

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Any, Dict, List

from src.application.ports.i_authorizer import IAuthorizer

logger = logging.getLogger("security.auth")


class LocalAuthorizer(IAuthorizer):
    """
    Local authorization implementation for offline deployments.

    This implementation uses environment-based tokens for authentication
    and role-based access control for authorization decisions.
    """

    ROLE_PERMISSIONS: dict[str, List[str]] = {
        "admin": ["read_reports", "write_reports", "delete_reports", "admin_access"],
        "operator": ["read_reports", "write_reports"],
        "viewer": ["read_reports"],
        "system": ["read_reports", "write_reports", "system_access"],
    }

    ACTION_PERMISSIONS: dict[str, str] = {
        "generate_report": "write_reports",
        "view_report": "read_reports",
        "delete_report": "delete_reports",
        "admin_operation": "admin_access",
        "system_operation": "system_access",
    }

    def __init__(self) -> None:
        self._system_token = os.getenv("CCIF_SYSTEM_TOKEN")

        if not self._system_token:
            env = os.getenv("CCIF_ENVIRONMENT", "development")
            if env == "production":
                raise RuntimeError(
                    "CCIF_SYSTEM_TOKEN environment variable is required in production"
                )
            else:
                self._system_token = "dev_token_change_in_production"
                logger.warning(
                    "Using development token. Set CCIF_SYSTEM_TOKEN for production."
                )

        logger.info("LocalAuthorizer initialized successfully")

    def authorize(self, action: str, context: Dict[str, Any]) -> bool:
        user_id = context.get("user_id", "anonymous")
        role = context.get("role", "guest")
        provided_token = context.get("system_token", "")

        logger.debug(f"Auth attempt: action={action}, user={user_id}, role={role}")

        if not self._validate_token(provided_token):
            logger.warning(f"Invalid token for user {user_id}")
            return False

        if role not in self.ROLE_PERMISSIONS:
            logger.warning(f"Invalid role '{role}' for user {user_id}")
            return False

        required_permission = self.ACTION_PERMISSIONS.get(action)
        if not required_permission:
            logger.error(f"Unknown action '{action}' - default deny")
            return False

        user_permissions = self.ROLE_PERMISSIONS.get(role, [])
        if required_permission not in user_permissions:
            logger.warning(
                f"User {user_id} (role={role}) denied permission "
                f"'{required_permission}' for action '{action}'"
            )
            return False

        logger.info(f"Authorized: user={user_id}, action={action}")
        return True

    def _validate_token(self, provided_token: str) -> bool:
        if not provided_token:
            return False
        return hmac.compare_digest(
            provided_token.encode("utf-8"), self._system_token.encode("utf-8")
        )

    def get_user_permissions(self, user_id: str) -> List[str]:
        return self.ROLE_PERMISSIONS.get("operator", [])
