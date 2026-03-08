#!/usr/bin/env python3
"""
Ledger Event Taxonomy — تصنيف أحداث السجل الجنائي
✅ يغطي جميع العمليات التشغيلية
✅ قابل للتدقيق الجنائي (Forensic Audit)
✅ متوافق مع LanguageManager للترجمة
✅ يدعم التوسع المستقبلي
✅ متوافق مع verification_ledger.jsonl الحالي
✅ موحّد مع ledger_writer.append()

الإصدار: v1.2.0
تاريخ: 2026-02-27
الحالة: ✅ معتمد للإنتاج
"""

from enum import Enum


class LedgerEvent(Enum):
    """
    تصنيف شامل لأحداث Ledger — Production Ready

    ⚠️ مهم: القيم النصية يجب أن تطابق تماماً ما يُستخدم في ledger_writer.append()
    """

    # ═══════════════════════════════════════════════════════════════
    # عمليات FT2 (استيراد، تحقق، معالجة)
    # ═══════════════════════════════════════════════════════════════
    FT2_IMPORTED = "ft2_imported"
    FT2_PROCESSED = "ft2_processed"
    FILE_VALIDATED = "file_validated"
    FT2_ARCHIVED = "ft2_archived"
    FILE_ARCHIVED = "ft2_archived"  # alias for legacy code/tests
    SIGNATURE_VERIFIED = "signature_verified"
    SIGNATURE_INVALID = "signature_invalid"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"

    # ═══════════════════════════════════════════════════════════════
    # أحداث قديمة للتوافق مع الاختبارات (Backward Compatibility)
    # ═══════════════════════════════════════════════════════════════
    FILE_INGESTED = "file_ingested"  # ← للاختبارات القديمة
    FILE_CORRUPTED = "file_corrupted"  # ← للاختبارات القديمة
    PRE_VALIDATION_PASSED = "pre_validation_passed"  # ← للاختبارات القديمة
    PRE_VALIDATION_FAILED = "pre_validation_failed"  # ← للاختبارات القديمة
    AUTHENTICITY_VERIFIED = (
        "authenticity_verified"  # ← مستخدم في verify_and_record_uc.py ✅
    )
    AUTHENTICITY_FAILED = (
        "authenticity_failed"  # ← مستخدم في verify_and_record_uc.py ✅
    )
    ARCHIVE_VERIFIED = "archive_verified"  # ← للاختبارات القديمة
    ARCHIVE_VERIFY_FAILED = "archive_verify_failed"  # ← للاختبارات القديمة

    # ═══════════════════════════════════════════════════════════════
    # عمليات الربط بالأصول (من events.py)
    # ═══════════════════════════════════════════════════════════════
    ASSET_LINKED = "asset_linked"
    ASSET_REPLACED = "asset_replaced"
    FINAL_VERDICT_SAFE = "final_verdict_safe"
    FINAL_VERDICT_PARTIAL = "final_verdict_partial"
    FINAL_VERDICT_DISCARD = "final_verdict_discard"
    FILE_RETENTION_EXPIRED = "file_retention_expired"
    FILE_DELETED = "file_deleted"  # ← مستخدم في tests ✅
    FILE_QUARANTINED = "file_quarantined"

    # ═══════════════════════════════════════════════════════════════
    # عمليات التقارير (PDF، CSV، رسوم بيانية)
    # ═══════════════════════════════════════════════════════════════
    PDF_GENERATED = "pdf_generated"
    PDF_EXPORTED = "pdf_exported"
    REPORT_GENERATED = "report_generated"
    REPORT_OFFICIAL = "report_official"
    REPORT_ARABIC = "report_arabic"
    REPORT_TECHNICAL = "report_technical"
    CSV_EXPORTED = "csv_exported"
    CHART_GENERATED = "chart_generated"

    # ═══════════════════════════════════════════════════════════════
    # عمليات اللقاحات وسجل اللقاحات
    # ═══════════════════════════════════════════════════════════════
    VACCINE_REGISTRY_UPDATED = "vaccine_registry_updated"
    VACCINE_ADDED = "vaccine_added"
    VACCINE_EDITED = "vaccine_edited"
    VACCINE_DELETED = "vaccine_deleted"
    VACCINE_BATCH_REGISTERED = "vaccine_batch_registered"

    # ═══════════════════════════════════════════════════════════════
    # عمليات وحدات التبريد
    # ═══════════════════════════════════════════════════════════════
    UNIT_REGISTERED = "unit_registered"
    UNIT_EDITED = "unit_edited"
    UNIT_DELETED = "unit_deleted"
    TEMPERATURE_READING = "temperature_reading"

    # ═══════════════════════════════════════════════════════════════
    # عمليات الدورة (Cycle/Session Management)
    # ═══════════════════════════════════════════════════════════════
    CYCLE_STARTED = "cycle_started"
    CYCLE_COMPLETED = "cycle_completed"
    CYCLE_SAVED = "cycle_saved"
    CYCLE_LOADED = "cycle_loaded"
    CYCLE_EXPORTED = "cycle_exported"

    # ═══════════════════════════════════════════════════════════════
    # عمليات المشغل (Operator Sessions)
    # ═══════════════════════════════════════════════════════════════
    OPERATOR_SESSION_STARTED = "operator_session_started"
    OPERATOR_SESSION_ENDED = "operator_session_ended"
    OPERATOR_LOGIN = "operator_login"
    OPERATOR_LOGOUT = "operator_logout"
    OPERATOR_ACTION = "operator_action"

    # ═══════════════════════════════════════════════════════════════
    # الأخطاء والاستثناءات
    # ═══════════════════════════════════════════════════════════════
    ERROR_OCCURRED = "error_occurred"
    ERROR_CRITICAL = "error_critical"
    ERROR_RECOVERED = "error_recovered"
    LEDGER_APPEND_FAILED = "ledger_append_failed"
    LEDGER_CORRUPTED = "ledger_corrupted"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"

    # ═══════════════════════════════════════════════════════════════
    # أحداث النظام (System Events)
    # ═══════════════════════════════════════════════════════════════
    SYSTEM_STARTED = "system_started"
    SYSTEM_SHUTDOWN = "system_shutdown"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    CONFIG_CHANGED = "config_changed"
    LANGUAGE_CHANGED = "language_changed"

    # ═══════════════════════════════════════════════════════════════
    # أحداث التدقيق والأمان (Audit & Security)
    # ═══════════════════════════════════════════════════════════════
    AUDIT_STARTED = "audit_started"
    AUDIT_COMPLETED = "audit_completed"
    AUDIT_VERIFIED = "audit_verified"
    AUDIT_FAILED = "audit_failed"
    LEDGER_INTEGRITY_CHECK = "ledger_integrity_check"
    INTEGRITY_CHECK = "integrity_check"
    HASH_CHAIN_VALID = "hash_chain_valid"
    HASH_CHAIN_INVALID = "hash_chain_invalid"

    # ═══════════════════════════════════════════════════════════════
    # أحداث الترخيص (Licensing)
    # ═══════════════════════════════════════════════════════════════
    LICENSE_ACTIVATED = "license_activated"
    LICENSE_DEACTIVATED = "license_deactivated"
    LICENSE_EXPIRED = "license_expired"
    LICENSE_INVALID = "license_invalid"
    LICENSE_GUARD_CHECK = "license_guard_check"


# ───────────────────────────────────────────────────────────────
# قواميس لتصنيف الفئات والأولوية
# ───────────────────────────────────────────────────────────────
_EVENT_CATEGORY_PREFIX = {
    "ft2": "FT2",
    "signature": "FT2",
    "verification": "FT2",
    "file_ingested": "FT2",
    "file_validated": "FT2",
    "file_archived": "FT2",
    "pre_validation": "FT2",
    "authenticity": "FT2",
    "asset": "FT2",
    "pdf": "REPORT",
    "report": "REPORT",
    "csv": "REPORT",
    "chart": "REPORT",
    "final_verdict": "REPORT",
    "vaccine": "VACCINE",
    "unit": "UNIT",
    "temperature": "UNIT",
    "cycle": "CYCLE",
    "operator": "OPERATOR",
    "error": "ERROR",
    "file_corrupted": "ERROR",
    "file_not_found": "ERROR",
    "file_quarantined": "ERROR",
    "file_deleted": "ERROR",
    "system": "SYSTEM",
    "backup": "SYSTEM",
    "config": "SYSTEM",
    "language": "SYSTEM",
    "file_retention": "SYSTEM",
    "audit": "AUDIT",
    "integrity": "AUDIT",
    "hash": "AUDIT",
    "archive": "AUDIT",
    "license": "LICENSE",
}

_HIGH_PRIORITY_EVENTS = {
    LedgerEvent.ERROR_CRITICAL,
    LedgerEvent.LEDGER_CORRUPTED,
    LedgerEvent.SIGNATURE_INVALID,
    LedgerEvent.VERIFICATION_FAILED,
    LedgerEvent.HASH_CHAIN_INVALID,
    LedgerEvent.LICENSE_INVALID,
    LedgerEvent.PERMISSION_DENIED,
    LedgerEvent.FINAL_VERDICT_DISCARD,
    LedgerEvent.FILE_QUARANTINED,
    LedgerEvent.AUTHENTICITY_FAILED,
    LedgerEvent.ARCHIVE_VERIFY_FAILED,
    LedgerEvent.PRE_VALIDATION_FAILED,
}

_MEDIUM_PRIORITY_EVENTS = {
    LedgerEvent.ERROR_OCCURRED,
    LedgerEvent.LEDGER_APPEND_FAILED,
    LedgerEvent.FILE_NOT_FOUND,
    LedgerEvent.AUDIT_FAILED,
    LedgerEvent.CYCLE_COMPLETED,
    LedgerEvent.PDF_GENERATED,
    LedgerEvent.REPORT_GENERATED,
    LedgerEvent.FILE_VALIDATED,
    LedgerEvent.FILE_INGESTED,
    LedgerEvent.FILE_DELETED,
}


def get_event_category(event: LedgerEvent) -> str:
    for prefix, category in _EVENT_CATEGORY_PREFIX.items():
        if event.value.startswith(prefix):
            return category
    return "UNKNOWN"


def get_event_priority(event: LedgerEvent) -> str:
    if event in _HIGH_PRIORITY_EVENTS:
        return "HIGH"
    elif event in _MEDIUM_PRIORITY_EVENTS:
        return "MEDIUM"
    return "LOW"


EVENT_CATEGORY = {event: get_event_category(event) for event in LedgerEvent}
EVENT_PRIORITY = {event: get_event_priority(event) for event in LedgerEvent}


# ───────────────────────────────────────────────────────────────
# دالة للتحقق من وجود حدث قبل الاستخدام (للتطوير)
# ───────────────────────────────────────────────────────────────
def validate_event_name(event_name: str) -> bool:
    """
    التحقق من أن اسم الحدث موجود في LedgerEvent

    الاستخدام:
        if validate_event_name('file_ingested'):
            event = LedgerEvent.FILE_INGESTED
    """
    return any(e.value == event_name.lower() for e in LedgerEvent)


def get_event_by_name(event_name: str) -> LedgerEvent:
    """
    الحصول على LedgerEvent من اسم نصي

    الاستخدام:
        event = get_event_by_name('file_ingested')
    """
    event_name = event_name.lower()
    for event in LedgerEvent:
        if event.value == event_name:
            return event
    raise ValueError(
        f"حدث غير معروف: {event_name}. الأحداث المتاحة: {[e.value for e in LedgerEvent]}"
    )
