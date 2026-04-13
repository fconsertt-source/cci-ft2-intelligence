"""
exceptions.py
-------------
استثناءات طبقة التخزين.
يُستورد منها في أي مكان دون الحاجة لمعرفة التقنية المستخدمة.
"""


class StorageError(Exception):
    """الاستثناء الجذري لطبقة التخزين."""


class SessionNotFoundError(StorageError):
    """الجلسة المطلوبة غير موجودة."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: '{session_id}'")


class SchemaMismatchError(StorageError):
    """
    تغيّرت أعمدة إحدى الدفعات أثناء الكتابة.

    يُثار عند Schema Drift، وهو الحالة التي تختلف فيها
    أعمدة دفعة لاحقة عن أعمدة الدفعة الأولى.
    """

    def __init__(self, expected: list, got: list):
        self.expected = expected
        self.got = got
        super().__init__(
            f"Schema mismatch.\n"
            f"  Expected columns : {expected}\n"
            f"  Got columns      : {got}"
        )


class IntegrityError(StorageError):
    """فشل التحقق من سلامة الملف (SHA-256 لا يتطابق)."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Integrity check failed for session: '{session_id}'")


class StorageWriteError(StorageError):
    """خطأ عام أثناء عملية الكتابة."""