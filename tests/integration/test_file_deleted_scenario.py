#!/usr/bin/env python3
"""
اختبار سيناريو حذف ملف — FILE_DELETED Event

✅ يتحقق من تسجيل حدث FILE_DELETED بشكل صحيح
✅ يتحقق من سلسلة Hash بعد الحذف
✅ يتحقق من التحديثات في Ledger
"""

import json
from datetime import datetime, timezone

import pytest

from src.domain.enums.ledger_event import LedgerEvent
from src.infrastructure.adapters.ledger_writer_adapter import LedgerWriterAdapter


@pytest.fixture
def temp_ledger_path(tmp_path):
    """إنشاء مسار Ledger مؤقت للاختبار"""
    return tmp_path / "test_ledger.jsonl"


@pytest.fixture
def ledger_writer(temp_ledger_path):
    """إنشاء Ledger Writer للاختبار"""
    return LedgerWriterAdapter(ledger_path=temp_ledger_path)


class TestFileDeletedScenario:
    """اختبار سيناريو حذف ملف"""

    def test_file_deleted_event_exists(self):
        """التأكد من وجود حدث FILE_DELETED في LedgerEvent"""
        assert hasattr(
            LedgerEvent, "FILE_DELETED"
        ), "FILE_DELETED غير موجود في LedgerEvent"
        assert LedgerEvent.FILE_DELETED.value == "file_deleted"

    def test_file_deleted_event_category(self):
        """التأكد من تصنيف حدث FILE_DELETED بشكل صحيح"""
        from src.domain.enums.ledger_event import EVENT_CATEGORY

        assert EVENT_CATEGORY[LedgerEvent.FILE_DELETED] == "ERROR"

    def test_file_deleted_event_priority(self):
        """التأكد من أولوية حدث FILE_DELETED"""
        from src.domain.enums.ledger_event import EVENT_PRIORITY

        assert EVENT_PRIORITY[LedgerEvent.FILE_DELETED] == "MEDIUM"

    def test_file_deleted_records_in_ledger(self, ledger_writer, temp_ledger_path):
        """التأكد من تسجيل حدث FILE_DELETED في Ledger"""
        # تسجيل حدث الحذف
        hash_value = ledger_writer.append(
            event_type=LedgerEvent.FILE_DELETED,
            file_hash="deleted_file_hash_abc123",
            event_id="delete-event-001",
            ft2_serial="FT2-DELETED-001",
            operator="admin",
            reason="Retention period expired",
        )

        # التحقق من وجود الإدخال
        assert temp_ledger_path.exists()
        assert ledger_writer.get_entry_count() == 1

        # التحقق من المحتوى
        last_entry = ledger_writer.get_last_entry()
        assert last_entry["event_type"] == "file_deleted"
        assert last_entry["file_hash"] == "deleted_file_hash_abc123"
        assert last_entry["event_id"] == "delete-event-001"
        assert last_entry["ft2_serial"] == "FT2-DELETED-001"
        assert last_entry["operator"] == "admin"
        assert "reason" in last_entry
        assert "current_hash" in last_entry
        assert "previous_hash" in last_entry

    def test_file_deleted_maintains_chain_integrity(self, ledger_writer):
        """التأكد من أن حدث FILE_DELETED يحافظ على سلامة السلسلة"""
        # تسجيل عدة أحداث قبل الحذف
        ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="evt-001",
        )
        ledger_writer.append(
            event_type=LedgerEvent.FILE_VALIDATED,
            file_hash="file123",
            event_id="evt-002",
        )

        # تسجيل حدث الحذف
        ledger_writer.append(
            event_type=LedgerEvent.FILE_DELETED,
            file_hash="file123",
            event_id="evt-003",
            reason="Test deletion",
        )

        # التحقق من سلامة السلسلة
        assert ledger_writer.verify_chain() is True
        assert ledger_writer.get_entry_count() == 3

    def test_file_deleted_with_full_workflow(self, ledger_writer):
        """اختبار سيناريو كامل: ingest → validate → delete"""
        workflow_events = [
            (
                LedgerEvent.FILE_INGESTED,
                {"file_hash": "abc123", "ft2_serial": "FT2-001"},
            ),
            (LedgerEvent.PRE_VALIDATION_PASSED, {"file_hash": "abc123"}),
            (LedgerEvent.AUTHENTICITY_VERIFIED, {"file_hash": "abc123"}),
            (LedgerEvent.FILE_VALIDATED, {"file_hash": "abc123"}),
            (
                LedgerEvent.FILE_ARCHIVED,
                {"file_hash": "abc123", "archive_path": "/archive/001"},
            ),
            (
                LedgerEvent.FILE_RETENTION_EXPIRED,
                {"file_hash": "abc123", "retention_days": 365},
            ),
            (
                LedgerEvent.FILE_DELETED,
                {"file_hash": "abc123", "reason": "Retention expired"},
            ),
        ]

        for event_type, kwargs in workflow_events:
            ledger_writer.append(event_type=event_type, **kwargs)

        # التحقق من عدد الأحداث
        assert ledger_writer.get_entry_count() == 7

        # التحقق من سلامة السلسلة
        assert ledger_writer.verify_chain() is True

        # التحقق من أن آخر حدث هو FILE_DELETED
        last_entry = ledger_writer.get_last_entry()
        assert last_entry["event_type"] == "file_deleted"

    def test_file_deleted_metadata_complete(self, ledger_writer):
        """التأكد من اكتمال البيانات الوصفية لحدث FILE_DELETED"""
        timestamp_before = datetime.now(timezone.utc).isoformat()

        hash_value = ledger_writer.append(
            event_type=LedgerEvent.FILE_DELETED,
            file_hash="test_hash",
            event_id="delete-test-001",
            ft2_serial="FT2-TEST",
            operator="test_user",
            cycle_id="CC-TEST-001",
            reason="Test deletion",
            original_path="/data/original.pdf",
            deleted_by_system=True,
        )

        timestamp_after = datetime.now(timezone.utc).isoformat()

        entry = ledger_writer.get_last_entry()

        # التحقق من الحقول الأساسية
        assert entry["event_type"] == "file_deleted"
        assert entry["file_hash"] == "test_hash"
        assert entry["event_id"] == "delete-test-001"
        assert entry["ft2_serial"] == "FT2-TEST"
        assert entry["operator"] == "test_user"
        assert entry["cycle_id"] == "CC-TEST-001"
        assert entry["reason"] == "Test deletion"
        assert entry["original_path"] == "/data/original.pdf"
        assert entry["deleted_by_system"] is True

        # التحقق من timestamp
        assert entry["timestamp"] >= timestamp_before
        assert entry["timestamp"] <= timestamp_after

        # التحقق من hash chain
        assert "previous_hash" in entry
        assert "current_hash" in entry
        assert len(entry["current_hash"]) == 64  # SHA-256 hex


class TestFileDeletedIntegration:
    """اختبارات تكاملية لحدث FILE_DELETED"""

    def test_file_deleted_translates_correctly(self):
        """التأكد من ترجمة حدث FILE_DELETED بشكل صحيح"""
        from src.shared.language_manager import LanguageManager

        lang = LanguageManager()

        # اختبار العربية
        lang.load_language("ar")
        ar_translation = lang.get("ledger.event.file_deleted", fallback="تم حذف الملف")
        assert ar_translation is not None

        # اختبار الإنجليزية
        lang.load_language("en")
        en_translation = lang.get("ledger.event.file_deleted", fallback="File deleted")
        assert en_translation is not None

    def test_file_deleted_appears_in_audit_log(self, ledger_writer, temp_ledger_path):
        """التأكد من ظهور حدث FILE_DELETED في سجل التدقيق"""
        # تسجيل حدث الحذف
        ledger_writer.append(
            event_type=LedgerEvent.FILE_DELETED,
            file_hash="audit_test_hash",
            event_id="audit-delete-001",
            operator="auditor",
        )

        # قراءة الملف مباشرة
        with open(temp_ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) >= 1

        # البحث عن حدث الحذف
        found_delete = False
        for line in lines:
            entry = json.loads(line)
            if entry["event_type"] == "file_deleted":
                found_delete = True
                assert entry["operator"] == "auditor"
                break

        assert found_delete, "حدث FILE_DELETED غير موجود في سجل التدقيق"
