from enum import Enum, auto

class FileStatus(Enum):
    """
    دورة حياة الملف في النظام.
    Clean Architecture: Enum في Domain لا يعتمد على أي مكتبة خارجية.
    """
    PENDING     = "pending"      # وصل للـ Inbox، لم يُفحص بعد
    VALIDATED   = "validated"    # اجتاز التحقق من الهوية
    PROCESSING  = "processing"   # قيد المعالجة الآن
    PROCESSED   = "processed"    # اكتملت المعالجة بنجاح
    ARCHIVED    = "archived"     # نُقل للأرشيف
    QUARANTINED = "quarantined"  # مرفوض أو مشكوك فيه

    @property
    def is_terminal(self) -> bool:
        """الحالات النهائية — لا انتقال بعدها"""
        return self in (
            FileStatus.ARCHIVED,
            FileStatus.QUARANTINED
        )

    @property
    def can_process(self) -> bool:
        """هل يمكن معالجة الملف في هذه الحالة؟"""
        return self == FileStatus.VALIDATED

    @classmethod
    def can_transition_to(cls, current: "FileStatus", target: "FileStatus") -> bool:
        """التحقق من صحة الانتقال بين الحالات"""
        transitions = {
            cls.PENDING: {cls.VALIDATED, cls.QUARANTINED},
            cls.VALIDATED: {cls.PROCESSING, cls.QUARANTINED},
            cls.PROCESSING: {cls.PROCESSED, cls.QUARANTINED},
            cls.PROCESSED: {cls.ARCHIVED},
            cls.ARCHIVED: set(),
            cls.QUARANTINED: set(),
        }
        return target in transitions.get(current, set())
