class LedgerError(Exception):
    """أخطاء عامة في نظام السجل"""

    pass


class LedgerIntegrityError(LedgerError):
    """انتهاك سلامة السلسلة (hash mismatch)"""

    pass


class LedgerWriteError(LedgerError):
    """فشل في كتابة المدخلة"""

    pass


class LedgerStateCorruptedError(LedgerError):
    """تلف في حالة السلسلة (state file)"""

    pass
