# src/infrastructure/security/license_guard.py
"""
Implementation of ILicenseGuard, residing in the Infrastructure layer.
Handles actual license validation, interacting with repositories and providers.
"""
from src.infrastructure.security.encrypted_license_repository import EncryptedLicenseRepository
from src.infrastructure.security.fingerprint_provider import FingerprintProvider
from src.application.ports.i_license_guard import ILicenseGuard
import logging

logger = logging.getLogger(__name__)

class LicenseGuard(ILicenseGuard):
    """Concrete implementation of the license guard port."""
    def __init__(self, repo: EncryptedLicenseRepository, provider: FingerprintProvider):
        self.repo = repo
        self.provider = provider
    
    def ensure_active(self):
        """Checks if the license is active and valid for the current system."""
        logger.debug("LicenseGuard: Checking license status...")
        license_data = self.repo.get_license_data()
        fingerprint = self.provider.get_fingerprint()

        if not license_data or not fingerprint or license_data.get("status") != "active" or license_data.get("fingerprint") != fingerprint:
            logger.warning("License is not active or invalid.")
            raise PermissionError("License is not active or invalid for this system.")
        logger.info("License is active and valid.")