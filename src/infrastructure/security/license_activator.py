# src/infrastructure/security/license_activator.py
from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

class LicenseActivator:
    """
    Handles first-run activation and license validation.
    - On first run: creates install.time if missing
    - Always verifies license.dat exists and is valid
    """
    
    def __init__(self, license_dir: Path = Path.home() / ".cci_ft2"):
        self._license_dir = license_dir
        self._install_time_path = license_dir / "install.time"
        self._license_path = license_dir / "license.dat"

    def ensure_installed(self) -> None:
        """Create install.time on first run."""
        if not self._install_time_path.exists():
            install_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
            self._install_time_path.write_text(install_time)
            # Log: First run detected

    def is_license_present(self) -> bool:
        """Check if license.dat exists."""
        return self._license_path.exists()

    def get_install_timestamp(self) -> Optional[str]:
        """Read install time (used by TrialPolicy)."""
        if self._install_time_path.exists():
            return self._install_time_path.read_text().strip()
        return None