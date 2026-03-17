import json
from pathlib import Path
from typing import Optional

from src.domain.ledger.models import LedgerChainState


def load_chain_state(state_path: Path) -> LedgerChainState:
    """Load chain state from file, or return fresh state if not exists"""
    if not state_path.exists():
        return LedgerChainState()

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return LedgerChainState.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        from src.domain.ledger.exceptions import LedgerStateCorruptedError

        raise LedgerStateCorruptedError(f"Corrupted state file: {e}")


def save_chain_state(state: LedgerChainState, state_path: Path) -> None:
    """Atomically save chain state"""
    from .atomic_writer import atomic_write
    from .canonical_json import to_canonical_json

    content = to_canonical_json(state.to_dict())
    atomic_write(state_path, content)


def get_last_hash_from_ledger(ledger_path: Path) -> Optional[str]:
    """
    Extract the last entry's hash from the ledger file.
    Fallback mechanism if state file is missing.
    """
    if not ledger_path.exists():
        return None

    last_hash = None
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                last_hash = entry.get('current_hash')
            except json.JSONDecodeError:
                continue

    return last_hash
