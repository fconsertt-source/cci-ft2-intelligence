# src/infrastructure/security/fingerprint_provider.py
from __future__ import annotations
import platform
import uuid
import os
from typing import Protocol

class FingerprintProviderProtocol(Protocol):
    def get_machine_id(self) -> str: ...
    def get_os_uuid(self) -> str: ...
    def get_install_timestamp(self) -> str: ...

class SystemFingerprintProvider(FingerprintProviderProtocol):
    def get_machine_id(self) -> str:
        # Try DMI first, fallback to hostname
        dmi_path = "/sys/class/dmi/id/product_uuid"
        if os.path.exists(dmi_path):
            with open(dmi_path, "r") as f:
                return f.read().strip().lower()
        return platform.node().lower()

    def get_os_uuid(self) -> str:
        # Linux: /proc/sys/kernel/random/uuid
        uuid_path = "/proc/sys/kernel/random/uuid"
        if os.path.exists(uuid_path):
            with open(uuid_path, "r") as f:
                return f.read().strip()
        return str(uuid.getnode())

    def get_install_timestamp(self) -> str:
        # Will be set on first run and stored in ~/.cci_ft2/install.time
        install_file = os.path.expanduser("~/.cci_ft2/install.time")
        if os.path.exists(install_file):
            with open(install_file, "r") as f:
                return f.read().strip()
        return "1970-01-01T00:00:00Z"  # fallback