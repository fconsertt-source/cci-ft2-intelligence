import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.domain.ledger.models import LedgerEntry, LedgerChainState
from src.domain.ledger.events import LedgerEvent
from src.domain.ledger.exceptions import (
    LedgerIntegrityError, 
    LedgerWriteError,
    LedgerStateCorruptedError
)
from src.infrastructure.utils.atomic_writer import atomic_append, atomic_write
from src.infrastructure.utils.hash_chain import (
    load_chain_state, 
    save_chain_state, 
    get_last_hash_from_ledger
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
        signing_key: Optional = None
    ):
        self.ledger_path = ledger_path
        self.state_path = state_path or ledger_path.parent / '.ledger_state.json'
        self.enable_signing = enable_signing
        self.signing_key = signing_key
        
        # ✅ قفل لضمان thread safety
        self._lock = threading.Lock()
        
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
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    last_hash = entry.get('current_hash')
                    entry_count += 1
                except json.JSONDecodeError:
                    continue
        
        state = LedgerChainState(
            last_entry_hash=last_hash,
            entry_count=entry_count,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        save_chain_state(state, self.state_path)
        return state
    
    def append(
        self,
        event_type: LedgerEvent,
        file_hash: str,
        event_id: Optional[str] = None,
        **context
    ) -> LedgerEntry:
        """
        Append a new entry with hash chaining.
        
        ✅ Thread-safe: العملية بأكملها داخل lock
        ✅ Uses cached last hash للأداء
        """
        with self._lock:
            if event_id is None:
                event_id = str(uuid.uuid4())
            
            # الحصول على previous_hash من cache أو state
            previous_hash = self._cached_last_hash or self._chain_state.last_entry_hash
            
            # إنشاء entry مبدئي
            entry = LedgerEntry(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                file_hash=file_hash,
                **context
            )
            
            # ربط السلسلة وحساب hash النهائي
            final_entry = entry.with_computed_hash(previous_hash=previous_hash)
            
            # كتابة المدخلة في ledger (نفس تنسيق hash)
            data_to_write = final_entry._to_serializable_dict(include_current_hash=True)
            ledger_line = json.dumps(
                data_to_write,
                sort_keys=True,
                separators=(',', ':'),
                ensure_ascii=False
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
                last_updated=datetime.now(timezone.utc).isoformat()
            )
            
            try:
                save_chain_state(self._chain_state, self.state_path)
            except Exception as e:
                logger.error(f"Failed to update chain state: {e}")
            
            logger.debug("Ledger entry appended: %s -> %s", event_type.name, entry.event_id)
            
            return final_entry
    
    def get_chain_state(self) -> LedgerChainState:
        """Get current chain state"""
        return self._chain_state
    
    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify entire ledger integrity by re-computing hash chain"""
        if not self.ledger_path.exists():
            return True, None
        
        previous_hash = None
        line_number = 0
        
        try:
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
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
                            return False, f"Chain break at line {line_number}: previous_hash mismatch"
                        
                        # التحقق من صحة current_hash
                        if entry.current_hash != entry.compute_hash():
                            return False, f"Hash mismatch at line {line_number}"
                        
                        previous_hash = entry.current_hash
                        
                    except json.JSONDecodeError as e:
                        return False, f"Invalid JSON at line {line_number}: {e}"
                    except (TypeError, KeyError, ValueError) as e:
                        return False, f"Invalid entry structure at line {line_number}: {e}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error reading ledger: {e}"
    
    def get_entry(self, event_id: str) -> Optional[LedgerEntry]:
        """Retrieve entry by event_id"""
        if not self.ledger_path.exists():
            return None
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('event_id') == event_id:
                        return LedgerEntry.from_dict(data)
                except json.JSONDecodeError:
                    continue
        
        return None
