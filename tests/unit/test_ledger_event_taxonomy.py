#!/usr/bin/env python3
"""
اختبارات LedgerEvent Taxonomy

✅ تغطية شاملة لجميع الأحداث
✅ التحقق من التصنيف والأولوية
✅ اختبار التكامل مع Ledger Writer
"""

import json
from pathlib import Path

import pytest

from src.domain.enums.ledger_event import (
    EVENT_CATEGORY,
    EVENT_PRIORITY,
    LedgerEvent,
    get_event_category,
    get_event_priority,
)

# the project no longer has a subpackage 'ledger'; adapter lives at top of adapters
# and the concrete implementation is HashChainedLedgerWriter
from src.infrastructure.adapters.ledger_writer_adapter import (
    HashChainedLedgerWriter as LedgerWriterAdapter,
)


class TestLedgerEventEnum:
    """اختبارات LedgerEvent Enum"""

    def test_all_events_exist(self):
        """التأكد من وجود جميع الأحداث المطلوبة"""
        required_events = [
            # FT2
            "FT2_IMPORTED",
            "FT2_PROCESSED",
            "SIGNATURE_VERIFIED",
            # Reports
            "PDF_GENERATED",
            "REPORT_OFFICIAL",
            "REPORT_ARABIC",
            "REPORT_TECHNICAL",
            # Vaccines
            "VACCINE_REGISTRY_UPDATED",
            "VACCINE_ADDED",
            # Cycle
            "CYCLE_STARTED",
            "CYCLE_COMPLETED",
            # Operator
            "OPERATOR_SESSION_STARTED",
            "OPERATOR_SESSION_ENDED",
            # Errors
            "ERROR_OCCURRED",
            "ERROR_CRITICAL",
            # System
            "SYSTEM_STARTED",
            "BACKUP_CREATED",
            # Audit
            "AUDIT_STARTED",
            "AUDIT_COMPLETED",
            "AUDIT_VERIFIED",
            # License
            "LICENSE_ACTIVATED",
            "LICENSE_GUARD_CHECK",
        ]

        for event_name in required_events:
            assert hasattr(LedgerEvent, event_name), f"Missing event: {event_name}"

    def test_event_values_are_unique(self):
        """التأكد من أن قيم الأحداث فريدة"""
        values = [event.value for event in LedgerEvent]
        assert len(values) == len(set(values)), "Duplicate event values found"

    def test_event_values_are_lowercase_snake_case(self):
        """التأكد من أن القيم بصيغة snake_case"""
        import re

        # allow digits (e.g. ft2_imported)
        pattern = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")

        for event in LedgerEvent:
            assert pattern.match(event.value), f"Invalid format: {event.value}"


class TestEventCategory:
    """اختبارات تصنيف الأحداث"""

    def test_ft2_events_category(self):
        """أحداث FT2 يجب أن تكون في فئة FT2"""
        ft2_events = [
            LedgerEvent.FT2_IMPORTED,
            LedgerEvent.SIGNATURE_VERIFIED,
            LedgerEvent.VERIFICATION_PASSED,
        ]

        for event in ft2_events:
            assert get_event_category(event) == "FT2"

    def test_report_events_category(self):
        """أحداث التقارير يجب أن تكون في فئة REPORT"""
        report_events = [
            LedgerEvent.PDF_GENERATED,
            LedgerEvent.REPORT_OFFICIAL,
            LedgerEvent.CSV_EXPORTED,
        ]

        for event in report_events:
            assert get_event_category(event) == "REPORT"

    def test_vaccine_events_category(self):
        """أحداث اللقاحات يجب أن تكون في فئة VACCINE"""
        vaccine_events = [
            LedgerEvent.VACCINE_ADDED,
            LedgerEvent.VACCINE_REGISTRY_UPDATED,
        ]

        for event in vaccine_events:
            assert get_event_category(event) == "VACCINE"

    def test_error_events_category(self):
        """أحداث الأخطاء يجب أن تكون في فئة ERROR"""
        error_events = [
            LedgerEvent.ERROR_OCCURRED,
            LedgerEvent.ERROR_CRITICAL,
        ]

        for event in error_events:
            assert get_event_category(event) == "ERROR"


class TestEventPriority:
    """اختبارات أولوية الأحداث"""

    def test_critical_events_high_priority(self):
        """الأحداث الحرجة يجب أن تكون HIGH priority"""
        high_priority_events = [
            LedgerEvent.ERROR_CRITICAL,
            LedgerEvent.LEDGER_CORRUPTED,
            LedgerEvent.SIGNATURE_INVALID,
            LedgerEvent.HASH_CHAIN_INVALID,
        ]

        for event in high_priority_events:
            assert get_event_priority(event) == "HIGH"

    def test_normal_events_low_priority(self):
        """الأحداث العادية يجب أن تكون LOW priority"""
        low_priority_events = [
            LedgerEvent.SYSTEM_STARTED,
            LedgerEvent.LANGUAGE_CHANGED,
            LedgerEvent.OPERATOR_SESSION_STARTED,
        ]

        for event in low_priority_events:
            assert get_event_priority(event) == "LOW"


class TestLedgerWriterWithTaxonomy:
    """اختبارات Ledger Writer مع Taxonomy"""

    @pytest.fixture
    def ledger_path(self, tmp_path):
        path = tmp_path / "test_ledger.jsonl"
        yield path
        if path.exists():
            path.unlink()

    def test_append_with_taxonomy(self, ledger_path):
        """اختبار إضافة إدخال مع taxonomy كامل"""
        writer = LedgerWriterAdapter(ledger_path)

        # only include supported fields; extras removed
        event_hash = writer.append(
            event_type=LedgerEvent.PDF_GENERATED,
            file_hash="dummy-hash-000",
            ft2_serial="130600112764",
            event_id="test-event-001",
        )

        # التحقق من وجود الإدخال
        assert ledger_path.exists()
        # count manually since writer doesn't expose method
        with open(ledger_path, "r", encoding="utf-8") as f:
            assert sum(1 for l in f if l.strip()) == 1

        # التحقق من المحتوى داخل السطر الأول
        with open(ledger_path, "r", encoding="utf-8") as f:
            first = json.loads(f.readline())
        # event_type is stored as lowercase value
        assert first["event_type"] == "pdf_generated"
        assert first["ft2_serial"] == "130600112764"
        assert "current_hash" in first
        assert "previous_hash" in first

    def test_hash_chain_integrity(self, ledger_path):
        """اختبار سلامة سلسلة Hash"""
        # LedgerEvent already imported at module scope
        writer = LedgerWriterAdapter(ledger_path)

        # إضافة عدة إدخالات
        writer.append(
            event_type=LedgerEvent.CYCLE_STARTED, file_hash="f1", event_id="event-001"
        )
        writer.append(
            event_type=LedgerEvent.FT2_IMPORTED, file_hash="f2", event_id="event-002"
        )
        writer.append(
            event_type=LedgerEvent.PDF_GENERATED, file_hash="f3", event_id="event-003"
        )

        # التحقق من السلسلة (manually via LedgerEntry.verify_chain)
        # count lines in ledger for entry count
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        assert len(lines) == 3
        previous = None
        from src.domain.ledger.models import LedgerEntry

        # LedgerEvent available globally
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                # convert event_type string back to enum (prefer value but allow name)
                try:
                    entry["event_type"] = LedgerEvent(entry["event_type"])
                except ValueError:
                    entry["event_type"] = LedgerEvent[entry["event_type"]]
                obj = LedgerEntry(**entry)
                assert obj.verify_chain(previous_hash=previous) is True
                previous = obj.current_hash

    def test_multiple_event_types(self, ledger_path):
        """اختبار أنواع أحداث متعددة"""
        writer = LedgerWriterAdapter(ledger_path)

        # only event types needed for category checks; context not required
        events = [
            (LedgerEvent.OPERATOR_SESSION_STARTED, {}),
            (LedgerEvent.VACCINE_ADDED, {}),
            (LedgerEvent.UNIT_REGISTERED, {}),
            (LedgerEvent.AUDIT_STARTED, {}),
            (LedgerEvent.BACKUP_CREATED, {}),
        ]

        for idx, (event_type, kwargs) in enumerate(events, start=1):
            # include dummy file_hash per new signature
            kwargs["file_hash"] = f"hash-{idx}"
            writer.append(event_type=event_type, **kwargs)

        with open(ledger_path, "r", encoding="utf-8") as f:
            assert sum(1 for l in f if l.strip()) == 5

        # التحقق من الفئات باستخدام الـ enum مباشرة
        categories = []
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                # stored event_type may be lower-value; convert safely
                try:
                    evt = LedgerEvent(entry["event_type"])
                except ValueError:
                    evt = LedgerEvent[entry["event_type"]]
                categories.append(get_event_category(evt))
        assert "OPERATOR" in categories
        assert "VACCINE" in categories
        assert "UNIT" in categories
        assert "AUDIT" in categories
        assert "SYSTEM" in categories
