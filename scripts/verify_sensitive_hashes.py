#!/usr/bin/env python3
"""
يتحقق من أن الملفات الحساسة (DO_NOT_TOUCH.txt) لم تتغير.
"""
import hashlib
import json
import sys
from pathlib import Path

HASH_FILE = "sensitive_hashes.json"

if not Path(HASH_FILE).exists():
    print("❌ ملف sensitive_hashes.json غير موجود. تأكد من تشغيل الخطوة الأولى.")
    sys.exit(1)

with open(HASH_FILE) as f:
    expected = json.load(f)

failed = []
for filepath, expected_hash in expected.items():
    if not Path(filepath).exists():
        failed.append(f"⚠️  الملف {filepath} غير موجود (ربما تم حذفه).")
        continue
    current = hashlib.sha256(Path(filepath).read_bytes()).hexdigest()
    if current != expected_hash:
        failed.append(f"❌ {filepath} تغير! (hash mismatch)")

if failed:
    print("\n".join(failed))
    sys.exit(1)
else:
    print("✅ جميع الملفات الحساسة سليمة.")
    sys.exit(0)