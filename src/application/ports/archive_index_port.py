"""
واجهة مجردة لفهرسة الأرشيف.
"""

from __future__ import annotations

from typing import Protocol, Iterable
from datetime import datetime

from src.domain.entities.archive_record import ArchiveRecord, ArchiveStatus


class ArchiveIndexPort(Protocol):
    """واجهة مجردة لفهرسة الأرشيف"""
    
    def append_record(self, record: ArchiveRecord) -> None:
        """إضافة سجل جديد (append-only)"""
        ...
    
    def append_status_change(
        self,
        record_id: str,
        new_status: ArchiveStatus,
        reason: str = ""
    ) -> None:
        """تسجيل تغيير الحالة"""
        ...
    
    def get_expired(self, as_of: datetime) -> Iterable[ArchiveRecord]:
        """الحصول على الملفات المنتهية"""
        ...
    
    def get_by_device(self, device_id: str) -> Iterable[ArchiveRecord]:
        """الحصول على ملفات جهاز معين"""
        ...
    
    def get_by_status(self, status: ArchiveStatus) -> Iterable[ArchiveRecord]:
        """الحصول على ملفات بحالة معينة"""
        ...
    
    def get_all(self) -> Iterable[ArchiveRecord]:
        """الحصول على جميع السجلات"""
        ...
