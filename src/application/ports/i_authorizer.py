"""
Authorization Port Interface.

This module defines the abstraction for authorization logic, allowing
different implementations (Local, OAuth2, JWT) without changing business logic.

Principle: Dependency Inversion (Clean Architecture)
Security: CWE-287 (Improper Authentication)

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol


class IAuthorizer(Protocol):
    """
    Authorization Protocol for access control decisions.
    """

    def authorize(self, action: str, context: Dict[str, Any]) -> bool:
        """
        Authorize an action based on provided context.

        Args:
            action: The action being requested (e.g., "generate_report")
            context: Dictionary containing user context

        Returns:
            bool: True if authorized, False otherwise
        """
        ...

    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Retrieve permissions for a specific user.

        Args:
            user_id: The user identifier

        Returns:
            List of permission strings
        """
        ...
