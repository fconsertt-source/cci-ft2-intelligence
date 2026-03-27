#!/usr/bin/env python3
import sys
from pathlib import Path


def main():
    required_docs = [
        "README.md",
        "PRODUCTION_README.md",
        "docs/ADR-001-Ledger-Implementation.md",
    ]

    missing = []
    for doc in required_docs:
        if not Path(doc).exists():
            missing.append(doc)

    if missing:
        print("❌ Missing documentation:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    print("✅ All required documentation exists")
    sys.exit(0)


if __name__ == "__main__":
    main()
