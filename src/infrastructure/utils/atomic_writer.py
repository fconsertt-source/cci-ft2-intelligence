import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


# ============================================================
# 🔐 Cross-platform file locking
# ============================================================
if sys.platform == "win32":
    import msvcrt

    def _lock_fd(fd: int, timeout: float = 30.0) -> None:
        start = time.time()
        while True:
            try:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                return
            except OSError:
                if time.time() - start > timeout:
                    raise TimeoutError("Could not acquire file lock")
                time.sleep(0.05)

    def _unlock_fd(fd: int) -> None:
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass

else:
    import fcntl

    def _lock_fd(fd: int, timeout: float = 30.0) -> None:
        start = time.time()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except OSError:
                if time.time() - start > timeout:
                    raise TimeoutError("Could not acquire file lock")
                time.sleep(0.05)

    def _unlock_fd(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


# ============================================================
# 🧱 Atomic write (replace file)
# ============================================================
def atomic_write(file_path: PathLike, content: str) -> None:
    """
    Atomically write content to a file (replace existing).
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(fd)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ============================================================
# 📝 Atomic append
# ============================================================
def atomic_append(file_path: PathLike, content: str, timeout: float = 30.0) -> None:
    """
    Atomically append content to a file.
    Locks the file during append to prevent concurrent writes.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    fd = os.open(file_path, flags)
    try:
        _lock_fd(fd, timeout)
        os.write(fd, (content + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        _unlock_fd(fd)
        os.close(fd)


# ============================================================
# 📖 Atomic read
# ============================================================
def atomic_read(file_path: PathLike, timeout: float = 30.0) -> str:
    """
    Read file content safely while locking to avoid concurrent writes.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    flags = os.O_RDONLY
    fd = os.open(file_path, flags)
    try:
        _lock_fd(fd, timeout)
        with os.fdopen(fd, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            _unlock_fd(fd)
        except Exception:
            pass


# ============================================================
# 🔀 Atomic move (rename)
# ============================================================
def atomic_move(src: PathLike, dst: PathLike) -> None:
    """
    Atomically move/rename a file.
    """
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.replace(src, dst)  # Atomic on Windows/Linux
