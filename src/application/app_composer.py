"""Compatibility import for the composition root.

The actual composer lives in ``src.shared.app_composer`` so Application does
not import concrete Infrastructure implementations.
"""

from src.shared.app_composer import AppComposer

__all__ = ["AppComposer"]
