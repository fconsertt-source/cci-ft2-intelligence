"""
Presentation Layer — User-facing interfaces only (no business logic).

Exports:
  - reporting: Data formatting (CSV/PDF/HTML)
  - cli: Command-line interfaces (wiring only)
  - messages: Centralized MessageMap for all user text
"""

from . import reporting
from . import cli
from . import messages

__all__ = ["reporting", "cli", "messages"]
