import os
import tempfile
from pathlib import Path
from typing import Union


def atomic_append(file_path: Path, content: str, mode: str = 'a') -> None:
    """
    Atomically append content to a file.
    
    Uses write-to-temp-then-rename pattern for safety.
    For append operations, we use file locking + direct append
    since true atomic append isn't possible across all filesystems.
    """
    import fcntl
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, mode, encoding='utf-8') as f:
        # File lock for concurrent access protection
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(content)
            f.write('\n')  # Ensure newline separation
            f.flush()
            os.fsync(f.fileno())  # Force disk write
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def atomic_write(file_path: Path, content: str) -> None:
    """
    Atomically write content to a file (replace existing).
    
    Uses write-to-temp-then-rename pattern.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file in same directory (for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f'.{file_path.name}.',
        suffix='.tmp'
    )
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.replace(tmp_path, file_path)
        
    except Exception:
        # Cleanup on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise