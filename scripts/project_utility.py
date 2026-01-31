#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import fnmatch
from pathlib import Path

# الإعدادات
PROJECT_ROOT = Path(__file__).parent.parent
# allow importing `src` during script runs
sys.path.append(str(PROJECT_ROOT))

from src.infrastructure.logging import get_logger
logger = get_logger(__name__)
IGNORE_PATTERNS = [
    '.git', '__pycache__', '.venv', 'venv', '*.pyc', '.pytest_cache',
    'data/output/*', 'scripts/project_utility.py'
]

def get_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            sha256.update(block)
    return sha256.hexdigest()

def generate_tree(dir_path, indent=""):
    items = sorted([d for d in os.listdir(dir_path) if not any(fnmatch.fnmatch(d, p) for p in IGNORE_PATTERNS)])
    tree_output = ""
    for i, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        if os.path.isdir(path):
            tree_output += f"{indent}{connector}📂 {item}/\n"
            tree_output += generate_tree(path, indent + ("    " if is_last else "│   "))
        else:
            tree_output += f"{indent}{connector}📄 {item}\n"
    return tree_output

def create_manifest():
    manifest = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in IGNORE_PATTERNS)]
        for f in files:
            if any(fnmatch.fnmatch(f, p) for p in IGNORE_PATTERNS): continue
            file_path = Path(root) / f
            rel_path = file_path.relative_to(PROJECT_ROOT)
            manifest.append({
                "path": str(rel_path).replace('\\', '/'),
                "sha256": get_sha256(file_path)
            })
    return sorted(manifest, key=lambda x: x['path'])

def main():
    logger.info("🛡️ CCI-FT2 Intelligence - Project State Utility")
    logger.info("%s", "="*45)

    # 1. عرض الشجرة
    logger.info("\n🌳 Project Structure:")
    logger.info("%s", generate_tree(PROJECT_ROOT))

    # 2. إنشاء المانيفست
    manifest_data = create_manifest()
    manifest_file = PROJECT_ROOT / "docs" / "project_state_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=4, ensure_ascii=False)

    logger.info("✅ Manifest updated: %s", manifest_file)
    logger.info("📊 Total tracked files: %d", len(manifest_data))

if __name__ == "__main__":
    main()