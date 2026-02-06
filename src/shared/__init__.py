"""Shared utilities, DI and configuration.

Central place for dependency injection wiring and shared helpers.
Move shared DI/config code here when consolidating wiring into a Composition Root.
"""

from src.infrastructure.utils import config_loader

__all__ = ["config_loader"]
