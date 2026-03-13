#!/usr/bin/env python3
"""
أدوات توحيد المسارات - دعم Windows, WSL, POSIX
"""
import re
from pathlib import Path
from typing import Union


def normalize_user_path(path: Union[str, Path]) -> Path:
    """
    توحيد مسار المستخدم بغض النظر عن المصدر (Windows, WSL, POSIX).

    يدعم:
    - مسارات Windows: C:\\Users\\...
    - مسارات WSL: /mnt/c/Users/...
    - مسارات POSIX: /home/user/...
    - مسارات UNC: \\\\server\\share\\...
    - Drag-and-drop من أي مكان

    Args:
        path: المسار الخام من المستخدم

    Returns:
        Path موحد ونظيف
    """
    if isinstance(path, Path):
        path = str(path)

    path = path.strip().strip('"').strip("'")

    # تحويل مسارات WSL إلى Windows
    wsl_match = re.match(r"^/mnt/([a-zA-Z])(/.*)$", path)
    if wsl_match:
        drive = wsl_match.group(1).upper()
        rest = wsl_match.group(2).replace("/", "\\")
        path = f"{drive}:{rest}"
        return Path(path)

    # نعالج مسارات Windows التي قد تظهر على نظام POSIX (backslashes)
    # عن طريق استبدالها بشرطة مائلة عادية
    import os

    if os.name != "nt":
        if "\\" in path and not path.startswith("\\"):
            # افترض أنه مسار Windows عادي
            path = path.replace("\\", "/")

    # استخدام normpath لإزالة أي جزئيات غير ضرورية
    normalized = os.path.normpath(path)
    return Path(normalized)


def is_valid_ft2_path(path: Path) -> bool:
    """التحقق من أن المسار صالح لملفات FT2"""
    if not path.exists():
        return False
    return path.suffix.lower() in [".txt", ".pdf", ".csv"]


def get_safe_filename(name: str, max_length: int = 100) -> str:
    """إنشاء اسم ملف آمن بدون أحرف خاصة"""
    import re

    safe = re.sub(r'[<>:"/\\|?*]', "_", name)
    return safe[:max_length]
