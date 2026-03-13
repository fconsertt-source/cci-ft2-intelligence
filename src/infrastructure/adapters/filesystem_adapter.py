#!/usr/bin/env python3
"""
محول عمليات الملفات لنظام الملفات المحلي.
يدعم العمليات الذرية الآمنة للأرشفة الجنائية.
متوافق مع Windows/Linux/Mac
"""
from __future__ import annotations

import hashlib
import logging
import os
import time  # ✅ إضافة
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)
PathLike = Union[str, Path]


class FilesystemAdapter:
    """
    تطبيق عمليات الملفات لنظام الملفات المحلي.
    الضمانات:
    - عمليات ذرية (atomic)
    - fsync بعد الكتابة
    - تحقق من السلامة
    - Cross-platform compatible
    """

    def compute_hash(self, path: PathLike) -> str:
        """حساب SHA-256 للملف"""
        path = Path(path)
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def exists(self, path: PathLike) -> bool:
        """التحقق من وجود الملف"""
        return Path(path).exists()

    def get_size(self, path: PathLike) -> int:
        """الحصول على حجم الملف"""
        return Path(path).stat().st_size

    def move_atomic(self, src: PathLike, dst: PathLike) -> None:
        """
        نقل ذري للملف مع fsync للضمان الجنائي.
        التدفق:
        1. نسخ إلى ملف مؤقت (كتابة مباشرة)
        2. fsync للكتابة للقرص
        3. rename ذري
        4. fsync للمجلد (best-effort على Windows)
        5. حذف المصدر
        """
        src = Path(src)
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)

        # ✅ اسم مؤقت فريد لتجنب التعارض
        tmp_path = dst.with_name(f"{dst.name}.tmp.{os.getpid()}")

        try:
            # ✅ نسخ يدوي مع fsync أثناء الكتابة (متوافق مع Windows)
            with open(src, "rb") as fsrc, open(tmp_path, "wb") as fdst:
                while True:
                    buf = fsrc.read(8192)
                    if not buf:
                        break
                    fdst.write(buf)
                fdst.flush()
                os.fsync(fdst.fileno())

            # ✅ rename ذري
            os.replace(str(tmp_path), str(dst))

            # ✅ fsync للمجلد (best-effort على Windows)
            try:
                if hasattr(os, "O_DIRECTORY"):
                    dir_fd = os.open(str(dst.parent), os.O_DIRECTORY)
                    try:
                        os.fsync(dir_fd)
                    finally:
                        os.close(dir_fd)
            except (AttributeError, OSError):
                logger.debug("Directory fsync not supported on this platform")

            # ✅ حذف المصدر مع retry لـ Windows
            try:
                src.unlink()
            except PermissionError:
                time.sleep(0.1)
                if src.exists():
                    src.unlink()

        except Exception as e:
            # تنظيف الملف المؤقت إذا فشل
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except:
                    pass
            # ✅ لف الخطأ بـ RuntimeError لتوافق الاختبارات
            raise RuntimeError(f"Atomic move failed: {e}")

    def atomic_move(self, src: PathLike, dst: PathLike) -> None:
        """
        ✅ Alias لـ move_atomic للتوافق مع الاختبارات القديمة.
        """
        self.move_atomic(src, dst)  # ✅ بدون return

    def delete_secure(self, path: PathLike) -> None:
        """
        حذف آمن للملف (overwrite قبل الحذف).
        ملاحظة: هذا best-effort ولا يضمن الإزالة الكاملة على SSD.
        """
        path = Path(path)
        if not path.exists():
            return
        try:
            # Overwrite ببيانات عشوائية على أجزاء
            file_size = path.stat().st_size
            chunk_size = 1024 * 1024  # 1MB chunks
            with open(path, "r+b") as f:
                remaining = file_size
                while remaining > 0:
                    chunk = min(chunk_size, remaining)
                    f.write(os.urandom(chunk))
                    remaining -= chunk
                f.flush()
                os.fsync(f.fileno())
            # حذف
            path.unlink()
        except Exception:
            if path.exists():
                path.unlink()

    def delete(self, path: PathLike) -> None:
        """حذف عادي للملف"""
        path = Path(path)
        if path.exists():
            path.unlink()


# ✅ Alias للتوافق مع الاختبارات القديمة
SafeFileOperations = FilesystemAdapter
