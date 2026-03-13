import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.domain.enums.ledger_event import LedgerEvent
from src.domain.ledger.exceptions import LedgerIntegrityError
from src.domain.ledger.models import LedgerChainState, LedgerEntry
from src.infrastructure.adapters.ledger_writer_adapter import HashChainedLedgerWriter


@pytest.fixture
def temp_ledger_dir():
    """Provide temporary directory for ledger tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def ledger_writer(temp_ledger_dir):
    """Provide fresh ledger writer for each test"""
    ledger_path = temp_ledger_dir / "test_ledger.jsonl"
    state_path = temp_ledger_dir / ".test_state.json"
    return HashChainedLedgerWriter(ledger_path=ledger_path, state_path=state_path)


class TestLedgerEntry:

    def test_compute_hash_is_deterministic(self):
        """Hash should be identical for identical entries"""
        entry1 = LedgerEntry(
            event_id="test-1",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
        )
        entry2 = LedgerEntry(
            event_id="test-1",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
        )

        assert entry1.compute_hash() == entry2.compute_hash()

    def test_canonical_json_removes_whitespace(self):
        """Canonical JSON should have no extra whitespace"""
        entry = LedgerEntry(
            event_id="test",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
        )
        canonical = entry.to_canonical_json()

        # Should not contain spaces after separators
        assert ": " not in canonical
        assert ", " not in canonical

    def test_with_computed_hash_sets_fields(self):
        """with_computed_hash should set previous_hash and current_hash"""
        entry = LedgerEntry(
            event_id="test",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
        )

        result = entry.with_computed_hash(previous_hash="prev123")

        assert result.previous_hash == "prev123"
        assert result.current_hash is not None
        assert len(result.current_hash) == 64  # SHA-256 hex length

    def test_verify_chain_valid(self):
        """verify_chain should return True for valid chain"""
        entry = LedgerEntry(
            event_id="test",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
            previous_hash="prev123",
        ).with_computed_hash(previous_hash="prev123")

        assert entry.verify_chain(previous_hash="prev123") is True

    def test_verify_chain_invalid_previous(self):
        """verify_chain should fail if previous_hash doesn't match"""
        entry = LedgerEntry(
            event_id="test",
            event_type=LedgerEvent.FILE_INGESTED,
            timestamp="2026-02-24T10:00:00Z",
            file_hash="abc123",
            previous_hash="prev123",
        ).with_computed_hash(previous_hash="prev123")

        assert entry.verify_chain(previous_hash="wrong_hash") is False


class TestHashChainedLedgerWriter:

    def test_append_creates_chained_entry(self, ledger_writer):
        """Append should create entry with proper hash chain"""
        entry = ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )

        assert entry.event_id == "event-001"
        assert entry.file_hash == "file123"
        assert entry.previous_hash is None  # First entry
        assert entry.current_hash is not None

    def test_append_chains_entries(self, ledger_writer):
        """Second entry should reference first entry's hash"""
        entry1 = ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )

        entry2 = ledger_writer.append(
            event_type=LedgerEvent.AUTHENTICITY_VERIFIED,
            file_hash="file123",
            event_id="event-002",
        )

        assert entry2.previous_hash == entry1.current_hash

    def test_append_is_atomic(self, ledger_writer):
        """Append should write complete lines only"""
        ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )

        # Read ledger and verify format
        with open(ledger_writer.ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1
        assert lines[0].strip()  # Non-empty
        assert json.loads(lines[0])  # Valid JSON

    def test_verify_integrity_valid_chain(self, ledger_writer):
        """verify_integrity should pass for valid chain"""
        ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )
        ledger_writer.append(
            event_type=LedgerEvent.AUTHENTICITY_VERIFIED,
            file_hash="file123",
            event_id="event-002",
        )

        is_valid, error = ledger_writer.verify_integrity()

        assert is_valid is True
        assert error is None

    def test_get_entry_retrieves_by_id(self, ledger_writer):
        """get_entry should find entry by event_id"""
        ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
            ft2_serial="FT2-12345",
        )

        entry = ledger_writer.get_entry("event-001")

        assert entry is not None
        assert entry.ft2_serial == "FT2-12345"

    def test_get_entry_returns_none_for_missing(self, ledger_writer):
        """get_entry should return None for non-existent ID"""
        entry = ledger_writer.get_entry("non-existent")
        assert entry is None

    def test_chain_state_updates_on_append(self, ledger_writer):
        """Chain state should reflect new entries"""
        initial_state = ledger_writer.get_chain_state()
        assert initial_state.entry_count == 0

        ledger_writer.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )

        updated_state = ledger_writer.get_chain_state()
        assert updated_state.entry_count == 1
        assert updated_state.last_entry_hash is not None

    def test_state_persists_across_instances(self, temp_ledger_dir):
        """Chain state should persist when creating new writer instance"""
        ledger_path = temp_ledger_dir / "test_ledger.jsonl"
        state_path = temp_ledger_dir / ".test_state.json"

        # First writer: add entry
        writer1 = HashChainedLedgerWriter(
            ledger_path=ledger_path, state_path=state_path
        )
        entry1 = writer1.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash="file123",
            event_id="event-001",
        )

        # Second writer: should load existing state
        writer2 = HashChainedLedgerWriter(
            ledger_path=ledger_path, state_path=state_path
        )
        entry2 = writer2.append(
            event_type=LedgerEvent.AUTHENTICITY_VERIFIED,
            file_hash="file123",
            event_id="event-002",
        )

        # Chain should be continuous
        assert entry2.previous_hash == entry1.current_hash
