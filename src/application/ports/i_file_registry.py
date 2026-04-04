"""
Port (Interface) لسجل الملفات المعالجة.

Clean Architecture:
- Application يعرّف الواجهة (Port)
- Infrastructure تُنفّذها (Adapter)
- Domain لا يعلم بوجود هذه الواجهة
"""
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class IFileRegistry(ABC):

    @abstractmethod
    def is_processed(self, file_hash: str) -> bool:
        """هل سبق معالجة هذا الملف؟ (Idempotency Check)"""
        ...

    @abstractmethod
    def mark_processed(self, file_hash: str, device_id: str, run_id: str, processed_at: datetime) -> None:
        """سجّل الملف كمعالَج بعد نجاح المعالجة."""
        ...

    @abstractmethod
    def get_run_files(self, run_id: str) -> list[str]:
        """جلب جميع ملفات تشغيل محدد (للـ Rollback)."""
        ...

    @abstractmethod
    def mark_quarantined(self, file_hash: str, reason_ar: str, reason_en: str) -> None:
        """سجّل الملف كمحجور مع سبب الرفض."""
        ...