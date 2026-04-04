"""
File Lock Service: يمنع المعالجة المتزامنة لنفس الملف.
يعتمد على filelock (موجود في venv بالفعل).
"""
from contextlib import contextmanager
from pathlib import Path
from filelock import FileLock, Timeout

LOCK_TIMEOUT = 30  # ثانية

class FileLockService:

    def __init__(self, lock_dir: Path):
        self._lock_dir = lock_dir
        lock_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock_file(self, file_path: Path):
        """
        Context Manager: يقفل ملفاً أثناء معالجته.
        يرفع FileLockError إذا كان الملف محجوزاً.
        """
        lock_path = self._lock_dir / f"{file_path.name}.lock"
        lock = FileLock(lock_path, timeout=LOCK_TIMEOUT)

        try:
            with lock.acquire():
                yield
        except Timeout:
            raise RuntimeError(f"الملف محجوز لمعالجة أخرى: {file_path.name} (انتظر {LOCK_TIMEOUT} ثانية)")
        finally:
            # حذف ملف القفل بعد الانتهاء
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)