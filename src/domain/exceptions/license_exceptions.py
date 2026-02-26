"""
Custom exceptions for the license and security subsystem.
"""

class LicenseError(Exception):
    """Base class for all license-related errors."""
    pass

class LicenseExpiredError(LicenseError):
    """Raised when a trial or fixed-term license has expired."""
    pass

class LicenseTamperedError(LicenseError):
    """
    Raised when the license signature is invalid, indicating it has been
    modified after being issued.
    """
    pass

class IntegrityError(LicenseError):
    """
    Raised for general integrity failures, such as when the encrypted payload
    cannot be decrypted, suggesting corruption or a key mismatch.
    """
    pass

class FingerprintError(LicenseError):
    """Raised when the machine fingerprint does not match the one in the license."""
    pass

class ExtractionError(Exception):
    """خطأ في استخراج البيانات من مصدر خارجي (PDF، TXT، إلخ)"""
    pass

class SecurityViolation(Exception):
    """انتهاك أمني (توقيع غير صالح، بيانات معدلة، إلخ)"""
    pass
