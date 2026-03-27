#!/usr/bin/env python3
"""
اختبار تزامن عالي الإجهاد لـ Ledger Writer

يكشف:
- interleaved writes
- corrupted JSONL
- lock starvation
"""

import importlib.util
import multiprocessing as mp
from pathlib import Path

import pytest

# skip entire module if filelock isn't installed (required for cross-process safety)
if importlib.util.find_spec("filelock") is None:
    pytest.skip(
        "filelock not installed - skipping cross-process concurrency tests",
        allow_module_level=True,
    )

from src.domain.enums.ledger_event import LedgerEvent
from src.infrastructure.adapters.ledger_writer_adapter import \
    HashChainedLedgerWriter


def write_worker(ledger_path: Path, worker_id: int, iterations: int):
    """عامل كتابة متوازي"""
    writer = HashChainedLedgerWriter(ledger_path=ledger_path)
    for i in range(iterations):
        writer.append(
            event_type=LedgerEvent.LEDGER_INTEGRITY_CHECK,
            file_hash=f"worker-{worker_id}-entry-{i}",
            event_id=f"test-{worker_id}-{i}",
            ft2_serial=f"TEST-{worker_id}",
        )


def test_concurrent_ledger_writes(tmp_path):
    """اختبار كتابة متوازية من 4 عمليات"""
    ledger_path = tmp_path / "concurrent_test_ledger.jsonl"

    processes = []
    for worker_id in range(4):
        p = mp.Process(target=write_worker, args=(ledger_path, worker_id, 25))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # التحقق من سلامة السلسلة
    # إعادة تحميل الكاتب ونفّذ فحص التكامل
    ledger = HashChainedLedgerWriter(ledger_path=ledger_path)
    is_valid, error = ledger.verify_integrity()
    assert is_valid, f"Ledger corrupted: {error}"

    # يجب أن يحتوي الملف على 100 سطر (25*4)
    with open(ledger_path, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    assert len(lines) == 100, f"Expected 100 entries, got {len(lines)}"
