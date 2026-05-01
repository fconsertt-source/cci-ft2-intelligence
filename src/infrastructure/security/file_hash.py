import hashlib
from pathlib import Path

def compute_file_hash(file_path: Path) -> str:
    """
    SHA-256 لمحتوى الملف الكامل.
    SSOT: كل hash يمر من هنا فقط.
    """
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def verify_file_integrity(
    file_path: Path,
    expected_hash: str
) -> bool:
    """التحقق من سلامة الملف بمقارنة Hash."""
    return compute_file_hash(file_path) == expected_hash