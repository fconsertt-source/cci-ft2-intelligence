#!/usr/bin/env python3
"""
التحقق الجنائي من سلامة سجل التدقيق (Ledger Integrity Audit)

هذا السكريبت:
1. يعيد حساب سلسلة الـ hash للتحقق من عدم التلاعب
2. يكشف أي كسر في السلسلة أو mismatch في الـ hashes
3. يسجل نتيجة التدقيق في الـ ledger نفسه
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.enums.ledger_event import LedgerEvent
from src.shared.di_container import configure_ledger

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    project_root = Path(__file__).parent.parent
    ledger_path = project_root / "data" / "ledger" / "verification_ledger.jsonl"

    if not ledger_path.exists():
        logger.warning(f"Ledger not found: {ledger_path}")
        logger.info("✅ Empty ledger is considered valid")
        sys.exit(0)

    logger.info(f"🔍 Auditing Ledger: {ledger_path}")
    logger.info(f"📅 Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # تهيئة Ledger للتحقق
    ledger = configure_ledger(ledger_path)

    # إجراء التحقق
    is_valid, error = ledger.verify_integrity()

    # ✅ تسجيل نتيجة التدقيق في الـ ledger (بدون metadata)
    audit_event_id = f"audit-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    if is_valid:
        # حدث نجاح التدقيق
        ledger.append(
            event_type=LedgerEvent.LEDGER_INTEGRITY_CHECK,
            file_hash="AUDIT_SUCCESS",
            event_id=audit_event_id,
            ft2_serial="AUDIT_SYSTEM",
        )
    else:
        # حدث فشل التدقيق
        ledger.append(
            event_type=LedgerEvent.ARCHIVE_VERIFY_FAILED,
            file_hash="AUDIT_FAILURE",
            event_id=audit_event_id,
            ft2_serial="AUDIT_SYSTEM",
            # ✅ نستخدم حقول موجودة بدلاً من metadata
            authenticity_status=error[:100] if error else "Unknown error",
        )

    # عرض النتائج
    if is_valid:
        logger.info("✅ LEDGER INTEGRITY VERIFIED")
        logger.info("   🛡️  Chain of custody intact")
        logger.info("   🔗 No tampering detected")

        state = ledger.get_chain_state()
        logger.info(f"   📊 Entries: {state.entry_count}")
        logger.info(
            f"   🔐 Last Hash: {state.last_entry_hash[:16] if state.last_entry_hash else 'None'}..."
        )

        sys.exit(0)
    else:
        logger.critical("❌ LEDGER INTEGRITY FAILED")
        logger.critical(f"   🚨 Error: {error}")
        logger.critical("   ⚠️  Potential tampering or corruption detected")
        logger.critical("   🔍 Immediate forensic investigation recommended")

        sys.exit(1)


if __name__ == "__main__":
    main()
