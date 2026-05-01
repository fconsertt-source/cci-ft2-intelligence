from dataclasses import dataclass, replace
from datetime import datetime
from typing import FrozenSet
from src.domain.enums.file_status import FileStatus

@dataclass(frozen=True)
class FileIngestionRecord:
    """
    Value Object يمثل هوية الملف في دورة حياته.

    Clean Architecture:
    - frozen=True: Value Objects غير قابلة للتعديل
    - Domain لا يعرف المسار الفيزيائي للملف
    - يعتمد على Hash وليس الاسم (يمنع إعادة المعالجة)
    """
    file_hash: str        # SHA-256 — الهوية الثابتة للمحتوى
    device_id: str        # مستخرج من الملف، ليس من الاسم
    center_id: str        # مستخرج بعد التحقق من YAML
    ingested_at: datetime
    status: FileStatus = FileStatus.PENDING

    def __post_init__(self):
        if not self.file_hash or len(self.file_hash) != 64:
            raise ValueError(
                f"file_hash يجب أن يكون SHA-256 (64 حرفاً): {self.file_hash}"
            )
        if not self.device_id or len(self.device_id) < 6:
            raise ValueError(
                f"device_id غير صالح: {self.device_id}"
            )

    def is_already_processed(self) -> bool:
        return self.status in (
            FileStatus.PROCESSED,
            FileStatus.ARCHIVED
        )

    def belongs_to_registered_center(
        self,
        registered_device_ids: FrozenSet[str]
    ) -> bool:
        """SSOT Check: هل الجهاز مسجل في YAML؟ إذا لا → الملف يذهب للـ Quarantine فوراً."""
        return self.device_id in registered_device_ids

    def transition_to(
        self, new_status: FileStatus
    ) -> "FileIngestionRecord":
        """ينتج Value Object جديداً بالحالة الجديدة. لا يُعدّل الحالي (immutability)."""
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"انتقال غير صالح: {self.status} → {new_status}")
        return replace(self, status=new_status)