"""
تطبيق الفهرس باستخدام JSONL append-only.

المزايا:
- لا إعادة كتابة كاملة
- آمن للتوازي (مع قفل)
- قابل لإعادة البناء من Ledger
- بسيط وقابل للاستبدال بـ SQLite لاحقاً
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, Optional

from filelock import FileLock

from src.application.ports.archive_index_port import ArchiveIndexPort
from src.domain.entities.archive_record import ArchiveRecord, ArchiveStatus

logger = logging.getLogger(__name__)


class JSONLIndexAdapter(ArchiveIndexPort):
    """
    تطبيق الفهرس باستخدام JSONL append-only.
    
    الضمانات:
    - append-only للسلامة الجنائية
    - file lock للتوازي الآمن
    - cache في الذاكرة للأداء
    - قابل لإعادة البناء من Ledger
    """
    
    def __init__(self, index_path: Path, max_cache_size: int = 200_000):
        """
        تهيئة الفهرس.
        
        Args:
            index_path: مسار ملف الفهرس
            max_cache_size: الحد الأقصى للسجلات في الكاش
        """
        self.index_path = Path(index_path)
        self.max_cache_size = max_cache_size
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache في الذاكرة للأداء
        self._cache: dict[str, ArchiveRecord] = {}
        self._load_cache()
    
    def _load_cache(self):
        """تحميل الفهرس إلى الذاكرة عند البدء"""
        if not self.index_path.exists():
            return
        
        with open(self.index_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    if entry.get('type') == 'RECORD':
                        record = ArchiveRecord.from_dict(entry)
                        self._cache[record.record_id] = record
                    
                    elif entry.get('type') == 'TOMBSTONE':
                        record_id = entry['record_id']
                        if record_id in self._cache:
                            old_record = self._cache[record_id]
                            new_status = ArchiveStatus(entry['new_status'])
                            self._cache[record_id] = old_record.transition_to(new_status)
                
                except Exception as e:
                    logger.warning("Failed to parse index line: %s", e)
        
        # تحذير إذا تجاوز الكاش الحد
        if len(self._cache) > self.max_cache_size:
            logger.warning(
                "Index cache size (%d) exceeded recommended limit (%d)",
                len(self._cache), self.max_cache_size
            )
    
    def _append_entry(self, entry: dict):
        """إضافة مدخلة للفهرس (append-only)"""
        lock_path = self.index_path.with_suffix('.lock')
        
        with FileLock(lock_path, timeout=60):
            with open(self.index_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                f.flush()
    
    def append_record(self, record: ArchiveRecord) -> None:
        """إضافة سجل جديد"""
        entry = {
            'type': 'RECORD',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **record.to_dict()
        }
        
        self._append_entry(entry)
        self._cache[record.record_id] = record
    
    def append_status_change(
        self,
        record_id: str,
        new_status: ArchiveStatus,
        reason: str = ""
    ) -> None:
        """تسجيل تغيير الحالة"""
        entry = {
            'type': 'TOMBSTONE',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'record_id': record_id,
            'new_status': new_status.value,
            'reason': reason
        }
        
        self._append_entry(entry)
        
        # تحديث cache
        if record_id in self._cache:
            old_record = self._cache[record_id]
            self._cache[record_id] = old_record.transition_to(new_status)
    
    def get_expired(self, as_of: datetime) -> Iterable[ArchiveRecord]:
        """الحصول على الملفات المنتهية"""
        now = as_of.isoformat()
        
        for record in self._cache.values():
            if record.status == ArchiveStatus.ARCHIVED and record.expires_at < now:
                yield record
    
    def get_by_device(self, device_id: str) -> Iterable[ArchiveRecord]:
        """الحصول على ملفات جهاز معين"""
        for record in self._cache.values():
            if record.device_id == device_id:
                yield record
    
    def get_by_status(self, status: ArchiveStatus) -> Iterable[ArchiveRecord]:
        """الحصول على ملفات بحالة معينة"""
        for record in self._cache.values():
            if record.status == status:
                yield record
    
    def get_all(self) -> Iterable[ArchiveRecord]:
        """الحصول على جميع السجلات"""
        return self._cache.values()
    
    def rebuild_from_ledger(self, ledger_events: Iterable[dict]) -> None:
        """
        إعادة بناء الفهرس من Ledger.
        
        يُستخدم عند تلف الفهرس أو للتحقق من الاتساق.
        """
        self._cache.clear()
        
        for event in ledger_events:
            event_type = event.get('event_type')
            
            if event_type == 'FILE_ARCHIVED':
                metadata = event.get('metadata', {})
                record = ArchiveRecord.create(
                    record_id=metadata.get('record_id', event.get('event_id', '')),
                    device_id=event.get('ft2_serial', 'UNKNOWN'),
                    file_hash=event.get('file_hash', ''),
                    file_size=metadata.get('file_size', 0),
                    original_path=event.get('source_path', ''),
                    archive_path=event.get('destination_path', ''),
                    retention_days=metadata.get('retention_days', 90)
                )
                self._cache[record.record_id] = record
            
            elif event_type == 'FILE_DELETED':
                # البحث عن السجل وتحديث حالته
                for record_id, record in list(self._cache.items()):
                    if record.archive_path == event.get('source_path'):
                        self._cache[record_id] = record.transition_to(ArchiveStatus.DELETED)
        
        # إعادة كتابة الفهرس كاملاً
        self._rebuild_index_file()
    
    def _rebuild_index_file(self):
        """إعادة كتابة ملف الفهرس من الـ cache"""
        backup_path = self.index_path.with_suffix('.backup')
        
        # نسخة احتياطية
        if self.index_path.exists():
            self.index_path.rename(backup_path)
        
        # كتابة جديدة
        with open(self.index_path, 'w', encoding='utf-8') as f:
            for record in self._cache.values():
                entry = {
                    'type': 'RECORD',
                    'timestamp': record.archived_at,
                    **record.to_dict()
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # حذف النسخة الاحتياطية بعد النجاح
        if backup_path.exists():
            backup_path.unlink()
