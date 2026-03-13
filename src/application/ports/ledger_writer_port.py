# src/application/ports/ledger_writer_port.py

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.enums.ledger_event import LedgerEvent
from src.domain.ledger.models import LedgerChainState, LedgerEntry


class LedgerWriterPort(Protocol):
    """
    Port for writing forensically-defensible audit entries.

    Guarantees:
    - Hash chaining for tamper evidence
    - Atomic writes for crash resilience
    - Append-only semantics
    """

    def append(
        self, event_type: LedgerEvent, file_hash: str, event_id: str, **context
    ) -> LedgerEntry:
        """
        Append a new entry to the ledger with hash chaining.

        Args:
            event_type: Type of event being recorded
            file_hash: SHA-256 of the file being processed
            event_id: Unique identifier for this event
            **context: Additional contextual data (ft2_serial, asset_id, etc.)

        Returns:
            The created LedgerEntry with computed hashes

        Raises:
            LedgerIntegrityError: If chain verification fails
            LedgerWriteError: If write operation fails
        """
        ...

    def get_chain_state(self) -> LedgerChainState:
        """Get current state of the hash chain"""
        ...

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify entire ledger integrity.

        Returns:
            (is_valid, error_message)
        """
        ...

    def get_entry(self, event_id: str) -> Optional[LedgerEntry]:
        """Retrieve a specific entry by ID"""
        ...
