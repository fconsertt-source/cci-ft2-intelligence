"""
اختبارات وحدة لكيان ArchiveRecord
"""

from datetime import datetime, timedelta, timezone

from src.domain.entities.archive_record import ArchiveRecord, ArchiveStatus


class TestArchiveRecord:
    """اختبارات كيان ArchiveRecord"""

    def test_create_record(self):
        """يجب إنشاء سجل بنجاح"""
        record = ArchiveRecord.create(
            device_id="130600112764",
            file_hash="abc123def456...",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/2026/02/device_130600112764/file.txt",
            retention_days=90,
        )

        assert record.record_id is not None
        assert record.device_id == "130600112764"
        assert record.file_hash == "abc123def456..."
        assert record.file_size == 1024
        assert record.status == ArchiveStatus.ARCHIVED
        assert record.retention_days == 90

    def test_is_expired_false(self):
        """يجب أن يكون غير منتهي الصلاحية عند الإنشاء"""
        record = ArchiveRecord.create(
            device_id="130600112764",
            file_hash="abc123",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/file.txt",
            retention_days=90,
        )

        assert record.is_expired is False

    def test_is_expired_true(self):
        """يجب أن يكون منتهي الصلاحية بعد المدة"""
        # إنشاء سجل منتهي يدوياً
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=100)).isoformat()
        future = (now - timedelta(days=10)).isoformat()

        record = ArchiveRecord(
            record_id="test-123",
            device_id="130600112764",
            file_hash="abc123",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/file.txt",
            archived_at=past,
            expires_at=future,  # انتهى منذ 10 أيام
            status=ArchiveStatus.ARCHIVED,
            retention_days=90,
        )

        assert record.is_expired is True

    def test_transition_to(self):
        """يجب الانتقال لحالة جديدة بشكل صحيح"""
        record = ArchiveRecord.create(
            device_id="130600112764",
            file_hash="abc123",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/file.txt",
        )

        # الانتقال لحالة DELETED
        new_record = record.transition_to(ArchiveStatus.DELETED)

        assert record.status == ArchiveStatus.ARCHIVED  # الأصلي لم يتغير
        assert new_record.status == ArchiveStatus.DELETED
        assert new_record.record_id == record.record_id  # نفس المعرف

    def test_to_dict_from_dict(self):
        """يجب التسلسل وإعادة البناء بشكل صحيح"""
        original = ArchiveRecord.create(
            device_id="130600112764",
            file_hash="abc123",
            file_size=1024,
            original_path="/input/file.txt",
            archive_path="/archive/file.txt",
        )

        # تسلسل
        data = original.to_dict()

        # إعادة بناء
        restored = ArchiveRecord.from_dict(data)

        assert restored.record_id == original.record_id
        assert restored.device_id == original.device_id
        assert restored.file_hash == original.file_hash
        assert restored.status == original.status
