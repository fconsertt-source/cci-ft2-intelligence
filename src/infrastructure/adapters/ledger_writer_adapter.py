# src/infrastructure/adapters/ledger_writer_adapter.py

import json
import logging
import os
import threading
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# filelock is required for cross-process safety
try:
    from filelock import FileLock
except ImportError:  # pragma: no cover
    # default to non-prod so unit/integration tests don't force installation
    if os.getenv("CCI_ENV", "dev") == "prod":
        raise RuntimeError(
            "filelock dependency missing - install with `pip install filelock` "
            "to enable cross-process ledger writes."
        )
    warnings.warn(
        "filelock missing - using no-op lock (unsafe for concurrency)",
        RuntimeWarning,
    )

    class FileLock:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False


from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.ledger.exceptions import (
    LedgerStateCorruptedError,
    LedgerWriteError,
)
from src.domain.ledger.models import LedgerChainState, LedgerEntry
from src.infrastructure.utils.atomic_writer import atomic_append
from src.infrastructure.utils.hash_chain import (
    get_last_hash_from_ledger,
    load_chain_state,
    save_chain_state,
)

logger = logging.getLogger(__name__)


class HashChainedLedgerWriter(LedgerWriterPort):
    """
    Production implementation of LedgerWriter with hash chaining.

    ✅ Thread-safe باستخدام threading.Lock
    ✅ Cached last hash للأداء
    ✅ Supports state_path للاستمرارية بين الجلسات
    """

    def __init__(
        self,
        ledger_path: Path,
        state_path: Optional[Path] = None,
        enable_signing: bool = False,
        signing_key: Optional = None,
    ):
        self.ledger_path = ledger_path
        self.state_path = state_path or ledger_path.parent / ".ledger_state.json"
        self.enable_signing = enable_signing
        self.signing_key = signing_key

        # ✅ قفل لضمان thread safety
        self._lock = threading.Lock()
        # ✅ file lock لضمان safety عبر عمليات متعددة
        lock_path = str(self.ledger_path) + ".lock"
        self._file_lock = FileLock(lock_path, timeout=60)

        # ✅ Cache لآخر hash للأداء
        self._cached_last_hash: Optional[str] = None

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._chain_state = self._load_or_init_state()

    def _load_or_init_state(self) -> LedgerChainState:
        """Load state from file, or compute from ledger if state missing"""
        try:
            state = load_chain_state(self.state_path)

            if self.ledger_path.exists() and state.entry_count > 0:
                last_hash = get_last_hash_from_ledger(self.ledger_path)
                if last_hash and last_hash != state.last_entry_hash:
                    logger.warning("State hash mismatch. Rebuilding state from ledger.")
                    return self._rebuild_state_from_ledger()

            return state

        except LedgerStateCorruptedError:
            logger.warning("State file corrupted. Rebuilding from ledger.")
            return self._rebuild_state_from_ledger()

    def _rebuild_state_from_ledger(self) -> LedgerChainState:
        """Rebuild chain state by scanning ledger file"""
        if not self.ledger_path.exists():
            return LedgerChainState()

        entry_count = 0
        last_hash = None

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    last_hash = entry.get("current_hash")
                    entry_count += 1
                except json.JSONDecodeError:
                    continue

        state = LedgerChainState(
            last_entry_hash=last_hash,
            entry_count=entry_count,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )
        save_chain_state(state, self.state_path)
        return state

    def append(
        self,
        event_type: LedgerEvent,
        file_hash: str,
        event_id: Optional[str] = None,
        **context,
    ) -> LedgerEntry:
        """
        Append a new entry with hash chaining.

        ✅ Thread-safe: العملية بأكملها داخل lock
        ✅ Uses cached last hash للأداء
        """
        # Acquire file lock first to prevent other processes from interleaving
        with self._file_lock:
            with self._lock:
                if event_id is None:
                    event_id = str(uuid.uuid4())

                # refresh previous_hash by reading ledger end (avoid stale cache)
                previous_hash = (
                    get_last_hash_from_ledger(self.ledger_path)
                    or self._chain_state.last_entry_hash
                )
                # update cache as well
                self._cached_last_hash = previous_hash

                # split context into fields known by LedgerEntry and extras
                from dataclasses import fields as _dc_fields

                constructor_fields = {f.name for f in _dc_fields(LedgerEntry) if f.init}
                init_kwargs = {}
                extra_kwargs = {}
                for k, v in context.items():
                    if k in constructor_fields:
                        init_kwargs[k] = v
                    else:
                        extra_kwargs[k] = v

                # إنشاء entry مبدئي مع الحقول المعروفة فقط
                entry = LedgerEntry(
                    event_id=event_id,
                    event_type=event_type,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    file_hash=file_hash,
                    **init_kwargs,
                )

                # ربط السلسلة وحساب hash النهائي
                final_entry = entry.with_computed_hash(previous_hash=previous_hash)

                # after lock: serialize and merge extra context values
                data_to_write = final_entry._to_serializable_dict(
                    include_current_hash=True
                )
                # extras go at top level to satisfy tests
                data_to_write.update(extra_kwargs)
                ledger_line = json.dumps(
                    data_to_write,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )

                try:
                    atomic_append(self.ledger_path, ledger_line)
                except Exception as e:
                    raise LedgerWriteError(f"Failed to write to ledger: {e}")

                # تحديث cache و state
                self._cached_last_hash = final_entry.current_hash
                self._chain_state = LedgerChainState(
                    last_entry_hash=final_entry.current_hash,
                    entry_count=self._chain_state.entry_count + 1,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                )

                try:
                    save_chain_state(self._chain_state, self.state_path)
                except Exception as e:
                    logger.error(f"Failed to update chain state: {e}")

                logger.debug(
                    "Ledger entry appended: %s -> %s", event_type.name, entry.event_id
                )

                return final_entry

    def get_chain_state(self) -> LedgerChainState:
        """Get current chain state"""
        return self._chain_state

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify entire ledger integrity by re-computing hash chain

        Returns a tuple (is_valid, error_message). This is the low-level
        implementation used by other helpers.
        """
        if not self.ledger_path.exists():
            return True, None

        previous_hash = None
        line_number = 0

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_number += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        entry = LedgerEntry.from_dict(data)

                        # التحقق من تسلسل previous_hash
                        if entry.previous_hash != previous_hash:
                            return (
                                False,
                                f"Chain break at line {line_number}: previous_hash mismatch",
                            )

                        # التحقق من صحة current_hash
                        if entry.current_hash != entry.compute_hash():
                            return False, f"Hash mismatch at line {line_number}"

                        previous_hash = entry.current_hash

                    except json.JSONDecodeError as e:
                        return False, f"Invalid JSON at line {line_number}: {e}"
                    except (TypeError, KeyError, ValueError) as e:
                        return (
                            False,
                            f"Invalid entry structure at line {line_number}: {e}",
                        )

            return True, None

        except Exception as e:
            return False, f"Error reading ledger: {e}"

    def get_entry(self, event_id: str) -> Optional[LedgerEntry]:
        """Retrieve entry by event_id"""
        if not self.ledger_path.exists():
            return None

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("event_id") == event_id:
                        return LedgerEntry.from_dict(data)
                except json.JSONDecodeError:
                    continue

        return None

    # ────────────────────────────────────────────────────────────
    # convenience helpers used by integration tests and scripts
    # ────────────────────────────────────────────────────────────
    def get_entry_count(self) -> int:
        """Return the number of entries currently in the ledger file."""
        return self._chain_state.entry_count or 0

    def get_last_entry(self) -> Optional[dict]:
        """Return the last ledger entry as a raw dict (not LedgerEntry).
        Useful for simple assertions in tests/scripts.
        """
        if not self.ledger_path.exists():
            return None
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return None
        try:
            return json.loads(lines[-1])
        except json.JSONDecodeError:
            return None

    def verify_chain(self) -> bool:
        """Simple boolean wrapper around :py:meth:`verify_integrity`.
        Legacy name kept for backwards compatibility with older tests/scripts.
        """
        valid, _ = self.verify_integrity()
        return valid


# backward compatibility for older integration tests and scripts
# previously this module exposed a class named LedgerWriterAdapter.
# tests/unit import `HashChainedLedgerWriter as LedgerWriterAdapter`,
# but some legacy code still expects the name directly.
LedgerWriterAdapter = HashChainedLedgerWriter
