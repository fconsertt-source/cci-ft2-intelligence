"""
Secure Value Objects for Input Validation and Sanitization.

Security Controls:
- CWE-20: Improper Input Validation
- CWE-78: OS Command Injection Prevention
- CWE-1333: Inefficient Regular Expression Complexity (ReDoS)

Author: Security Engineering Team
Version: 2.2.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class SecureID:
    """Secure identifier value object with validation."""

    MAX_LENGTH: Final[int] = 64
    MIN_LENGTH: Final[int] = 1
    PATTERN: Final[str] = r"^[a-zA-Z0-9_-]+$"

    value: str

    def __post_init__(self) -> None:
        self._validate_length()
        self._validate_format()

    def _validate_length(self) -> None:
        if not self.value or len(self.value) < self.MIN_LENGTH:
            raise ValueError(f"ID cannot be empty. Minimum length: {self.MIN_LENGTH}")
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(
                f"ID exceeds maximum length of {self.MAX_LENGTH} characters"
            )

    def _validate_format(self) -> None:
        if not re.match(self.PATTERN, self.value):
            raise ValueError(
                f"Invalid ID format: '{self.value}'. "
                f"Only alphanumeric, underscore, and hyphen allowed"
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"SecureID(value='{'*' * min(len(self.value), 8)}')"


@dataclass(frozen=True)
class SecureTimestamp:
    """Immutable secure timestamp for audit logging."""

    _value: str = field(init=False)
    _epoch: float = field(init=False)

    def __post_init__(self) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        object.__setattr__(self, "_value", now.isoformat())
        object.__setattr__(self, "_epoch", now.timestamp())

    @property
    def value(self) -> str:
        return self._value

    @property
    def epoch(self) -> float:
        return self._epoch

    def __str__(self) -> str:
        return self._value
