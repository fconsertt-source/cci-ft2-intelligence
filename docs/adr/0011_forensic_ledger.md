# ADR-0011: Forensic Ledger Implementation

## Status
✅ ACCEPTED

## Context
The system requires a tamper-evident audit trail to record all verification events and critical decisions regarding vaccine safety. Standard logging is insufficient for forensic purposes as it lacks immutability guarantees and chain-of-custody proof.

## Decision
We implemented a **Hash-Chained Ledger** (`HashChainedLedgerWriter`) with the following characteristics:

1.  **Hash Chaining**: Each entry contains the hash of the previous entry (`previous_hash`), creating an unbreakable chain similar to Blockchain.
2.  **Atomic Writes**: Uses `atomic_append` to ensure data integrity during concurrent writes or system crashes.
3.  **Thread Safety**: Implements `threading.Lock` to handle concurrent access safely.
4.  **State Persistence**: Caches the last hash in a separate state file (`.ledger_state.json`) for performance and continuity.
5.  **Canonical Serialization**: Enforces strict JSON serialization rules to ensure deterministic hashing.

## Consequences

### Positive
*   **Tamper Evidence**: Any modification to a past entry breaks the hash chain, making detection trivial via `verify_integrity()`.
*   **Legal Defensibility**: The records provide a strong chain of custody for digital evidence.
*   **Performance**: Caching the last hash avoids reading the entire file for every append.
*   **Simplicity**: Uses standard JSONL format, making it readable and easy to parse without specialized tools.

### Negative
*   **Append-Only**: modifying or deleting records is intentionally impossible/detectable.
*   **Strictness**: Requires strict adherence to serialization rules; manual editing of the ledger file will corrupt the chain.

## Compliance
*   Implements `LedgerWriterPort` (Clean Architecture).
*   Supports future RSA signing integration.