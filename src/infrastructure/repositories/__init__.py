"""Repository layer for domain-specific data access.

This package sits above the low-level adapters and exposes a cleaner
interface for application and presentation layers.  It currently contains
wrappers around JSON-based storage but can be extended as the project
matures.
"""

from .device_repository import DeviceDataRepository

__all__ = ["DeviceDataRepository"]
