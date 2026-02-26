"""
كيان سجل الأرشفة - Domain Entity نقي
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
import uuid


class ArchiveStatus(Enum):
    """حالات الملف في دورة الحياة"""
    PROCESSING = "PROCESSING"      # قيد المعالجة
    ARCHIVED = "ARCHIVED"          # مؤرشف بنجاح
    QUARANTINED = "QUARANTINED"    # مشكوك في سلامته
    EXPIRED = "EXPIRED"            # انتهت صلاحية الاحتفاظ
    DELETING = "DELETING"          # قيد الحذف
    DELETED = "DELETED"            # تم الحذف
    MISSING = "MISSING"            # مفقود (فشل التحقق)


@dataclass(frozen=True)
class ArchiveRecord:
    """
    كيان أرشيف نقي (بدون I/O).
    
    يمثل سجلاً واحداً في دورة حياة الملف.
    جميع الحقول immutable لضمان السلامة الجنائية.
    """
    
    record_id: str                          # UUID فريد
    device_id: str                          # معرف الجهاز
    file_hash: str                          # SHA-256
    file_size: int                          # حجم الملف بالبايت
    original_path: str                      # المسار الأصلي
    archive_path: str                       # مسار الأرشفة النهائي
    archived_at: str                        # ISO timestamp
    expires_at: str                         # ISO timestamp
    status: ArchiveStatus = ArchiveStatus.ARCHIVED
    retention_days: int = 90
    
    @classmethod
    def create(
        cls,
        device_id: str,
        file_hash: str,
        file_size: int,
        original_path: str,
        archive_path: str,
        retention_days: int = 90
    ) -> ArchiveRecord:
        """مصنع لإنشاء سجل جديد"""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=retention_days)
        
        return cls(
            record_id=str(uuid.uuid4()),
            device_id=device_id,
            file_hash=file_hash,
            file_size=file_size,
            original_path=str(original_path),
            archive_path=str(archive_path),
            archived_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            status=ArchiveStatus.ARCHIVED,
            retention_days=retention_days
        )
    
    @property
    def is_expired(self) -> bool:
        """هل انتهت مدة الاحتفاظ؟"""
        expiry = datetime.fromisoformat(self.expires_at)
        return datetime.now(timezone.utc) > expiry
    
    def transition_to(self, new_status: ArchiveStatus) -> ArchiveRecord:
        """الانتقال لحالة جديدة (immutable)"""
        return ArchiveRecord(
            record_id=self.record_id,
            device_id=self.device_id,
            file_hash=self.file_hash,
            file_size=self.file_size,
            original_path=self.original_path,
            archive_path=self.archive_path,
            archived_at=self.archived_at,
            expires_at=self.expires_at,
            status=new_status,
            retention_days=self.retention_days
        )
    
    def to_dict(self) -> dict:
        """تحويل السجل إلى قاموس للتسلسل"""
        return {
            'record_id': self.record_id,
            'device_id': self.device_id,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'original_path': self.original_path,
            'archive_path': self.archive_path,
            'archived_at': self.archived_at,
            'expires_at': self.expires_at,
            'status': self.status.value,
            'retention_days': self.retention_days
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ArchiveRecord:
        """إعادة بناء السجل من قاموس"""
        return cls(
            record_id=data['record_id'],
            device_id=data['device_id'],
            file_hash=data['file_hash'],
            file_size=data['file_size'],
            original_path=data['original_path'],
            archive_path=data['archive_path'],
            archived_at=data['archived_at'],
            expires_at=data['expires_at'],
            status=ArchiveStatus(data.get('status', 'ARCHIVED')),
            retention_days=data.get('retention_days', 90)
        )
