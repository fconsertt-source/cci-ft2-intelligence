#!/usr/bin/env python3
"""اختبار الانحدار للحسابات العلمية"""
import hashlib
import json
from pathlib import Path


def test_file_integrity():
    hashes = json.loads(Path("sensitive_hashes.json").read_text())
    for fp, eh in hashes.items():
        if Path(fp).exists():
            current = hashlib.sha256(Path(fp).read_bytes()).hexdigest()
            assert current == eh, f"❌ {fp} تغير!"
