"""
اختبارات وحدة لـ JSONLIndexAdapter
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.archive_record import ArchiveRecord, ArchiveStatus
from src.infrastructure.adapters.jsonl_index_adapter import JSONLIndexAdapter


@pytest.fixture
def adapter(tmp_path):
    """تهيئة adapter للاختبار"""
    index_path = tmp_path / "test_index.jsonl"
    return JSONLIndexAdapter(index_path)


@pytest.fixture
def sample_record():
    """إنشاء سجل اختبار"""
    return ArchiveRecord.create(
        device_id="130600112764",
        file_hash="abc123",
        file_size=1024,
        original_path="/input/file.txt",
        archive_path="/archive/file.txt",
        retention_days=90,
    )


class TestJSONLIndexAdapter:
    """اختبارات JSONLIndexAdapter"""

    def test_append_record(self, adapter, sample_record):
        """يجب إضافة سجل بنجاح"""
        adapter.append_record(sample_record)

        # التحقق من الكاش
        assert sample_record.record_id in adapter._cache

        # التحقق من الملف
        assert adapter.index_path.exists()

    def test_get_by_device(self, adapter, sample_record):
        """يجب الحصول على ملفات جهاز معين"""
        adapter.append_record(sample_record)

        records = list(adapter.get_by_device("130600112764"))

        assert len(records) == 1
        assert records[0].record_id == sample_record.record_id

    def test_get_expired(self, adapter):
        """يجب الحصول على الملفات المنتهية"""
        # إنشاء سجل منتهي
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=100)).isoformat()
        expired = (now - timedelta(days=10)).isoformat()

        expired_record = ArchiveRecord(
            record_id="expired-123",
            device_id="130600112764",
            file_hash="abc123",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/file.txt",
            archived_at=past,
            expires_at=expired,
            status=ArchiveStatus.ARCHIVED,
            retention_days=90,
        )

        adapter.append_record(expired_record)

        expired_files = list(adapter.get_expired(now))

        assert len(expired_files) == 1
        assert expired_files[0].record_id == "expired-123"

    def test_append_status_change(self, adapter, sample_record):
        """يجب تسجيل تغيير الحالة"""
        adapter.append_record(sample_record)

        # تغيير الحالة
        adapter.append_status_change(
            sample_record.record_id, ArchiveStatus.DELETED, reason="RETENTION_EXPIRED"
        )

        # التحقق من الكاش
        updated = adapter._cache[sample_record.record_id]
        assert updated.status == ArchiveStatus.DELETED

    def test_get_all(self, adapter, sample_record):
        """يجب الحصول على جميع السجلات"""
        adapter.append_record(sample_record)

        all_records = list(adapter.get_all())

        assert len(all_records) == 1
        assert all_records[0].record_id == sample_record.record_id
