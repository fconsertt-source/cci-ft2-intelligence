import threading

import pytest

from src.domain.enums.ledger_event import LedgerEvent
from src.infrastructure.adapters.ledger_writer_adapter import HashChainedLedgerWriter


@pytest.fixture
def production_style_ledger(tmp_path):
    """Ledger writer configured like production"""
    ledger_path = tmp_path / "verification_ledger.jsonl"
    return HashChainedLedgerWriter(ledger_path=ledger_path)


class TestLedgerIntegrity:

    def test_full_workflow_produces_valid_chain(self, production_style_ledger):
        """Simulate real workflow and verify chain integrity"""
        events = [
            (
                LedgerEvent.FILE_INGESTED,
                "file-abc",
                "evt-001",
                {"ft2_serial": "FT2-001"},
            ),
            (LedgerEvent.PRE_VALIDATION_PASSED, "file-abc", "evt-002", {}),
            (
                LedgerEvent.AUTHENTICITY_VERIFIED,
                "file-abc",
                "evt-003",
                {"alarm_detected": False},
            ),
            (LedgerEvent.FINAL_VERDICT_SAFE, "file-abc", "evt-004", {}),
        ]

        entries = []
        for event_type, file_hash, event_id, context in events:
            entry = production_style_ledger.append(
                event_type=event_type, file_hash=file_hash, event_id=event_id, **context
            )
            entries.append(entry)

        # Verify chain manually
        prev_hash = None
        for entry in entries:
            assert entry.previous_hash == prev_hash
            assert entry.current_hash == entry.compute_hash()
            prev_hash = entry.current_hash

        # Verify via built-in method
        is_valid, error = production_style_ledger.verify_integrity()
        assert is_valid, f"Integrity check failed: {error}"

    def test_tampered_ledger_detected(self, production_style_ledger):
        """Modifying ledger content should be detected"""
        # Create valid chain
        production_style_ledger.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="evt-001",
        )

        # Tamper with ledger file
        with open(production_style_ledger.ledger_path, "r+") as f:
            content = f.read()
            content = content.replace("file123", "TAMPERED")
            f.seek(0)
            f.write(content)
            f.truncate()

        # Integrity check should fail
        is_valid, error = production_style_ledger.verify_integrity()
        assert is_valid is False
        assert "Hash mismatch" in error or "chain break" in error.lower()

    def test_concurrent_appends_safe(self, production_style_ledger):
        """Multiple appends should maintain chain integrity"""
        errors = []

        def append_entry(idx):
            try:
                production_style_ledger.append(
                    event_type=LedgerEvent.FILE_INGESTED,
                    file_hash=f"file-{idx}",
                    event_id=f"evt-{idx:03d}",
                )
            except Exception as e:
                errors.append(e)

        # Simulate concurrent writes
        threads = [threading.Thread(target=append_entry, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent write errors: {errors}"

        # Verify final integrity
        is_valid, error = production_style_ledger.verify_integrity()
        assert is_valid, f"Chain integrity failed after concurrent writes: {error}"
