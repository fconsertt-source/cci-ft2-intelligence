#!/usr/bin/env python3
"""Create a timestamped backup of the project excluding build artifacts."""

import os
import sys
import tarfile
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.presentation.messages.message_map import MessageProvider


def create_backup():
    # تحديد المسارات
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    backup_dir = project_root / "backup"

    # إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
    backup_dir.mkdir(exist_ok=True)

    # اسم الملف مع التاريخ والوقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_{timestamp}.tar.gz"
    archive_path = backup_dir / archive_name

    print(MessageProvider.get("BACKUP_CREATION_START", name=project_root.name))
    print(MessageProvider.get("BACKUP_TARGET_PATH", path=archive_path))

    # قائمة المجلدات والملفات المستثناة
    EXCLUDES = {
        ".git",
        ".venv",
        "venv",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".qodo",
        ".idea",
        ".vscode",
        "backup",
        "dist",
        "build",
        ".tox",
        "pipeline.log",
    }

    def filter_func(tarinfo):
        name = os.path.basename(tarinfo.name.rstrip("/"))
        if name in EXCLUDES:
            return None
        if name.endswith(".pyc") or name.endswith(".pyo"):
            return None
        return tarinfo

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(project_root, arcname=project_root.name, filter=filter_func)

        size_mb = archive_path.stat().st_size / (1024 * 1024)
        print(MessageProvider.get("BACKUP_CREATION_SUCCESS"))
        print(MessageProvider.get("BACKUP_SIZE", size=size_mb))
        print(MessageProvider.get("BACKUP_LOCATION", path=archive_path))

    except Exception as e:
        print(MessageProvider.get("BACKUP_CREATION_FAILED", error=str(e)))
        if archive_path.exists():
            archive_path.unlink()


if __name__ == "__main__":
    create_backup()
