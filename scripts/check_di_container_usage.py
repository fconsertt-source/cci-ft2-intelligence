#!/usr/bin/env python3
"""Guard script: fail if DI container is used incorrectly.

Usage: run from repo root. Returns exit code 1 on violations.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
TARGET_DIRS = [
    os.path.join(ROOT, 'src', 'domain'),
    os.path.join(ROOT, 'src', 'application'),
    os.path.join(ROOT, 'src', 'infrastructure'),
    os.path.join(ROOT, 'src', 'presentation')
]

# Allowlisted directories that may need container access
ALLOWED_CONTAINER_ACCESS = [
    os.path.join(ROOT, 'src', 'presentation', 'cli'),
    os.path.join(ROOT, 'src', 'presentation', 'gui'),
    os.path.join(ROOT, 'scripts')
]

PATTERN = re.compile(
    r"\bfrom\s+src\.shared\.di|\bimport\s+src\.shared\.di|src\.shared\.di\."
)


def scan_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if PATTERN.search(line):
                return i, line.strip()
    return None


def main():
    violations = []
    for td in TARGET_DIRS:
        if not os.path.exists(td):
            continue
        for root, _, files in os.walk(td):
            # Skip allowed directories
            skip_root = False
            for allowed in ALLOWED_CONTAINER_ACCESS:
                if os.path.commonpath([root, allowed]) == allowed:
                    skip_root = True
                    break
            if skip_root:
                continue
            for fn in files:
                if not fn.endswith(('.py',)):
                    continue
                path = os.path.join(root, fn)
                res = scan_file(path)
                if res:
                    ln, snippet = res
                    violations.append((path, ln, snippet))

    if violations:
        print("ERROR: DI container imported in forbidden locations:")
        for path, ln, snippet in violations:
            rel_path = os.path.relpath(path, ROOT)
            print(f"  {rel_path}:{ln}: {snippet}")
        print("\nDI container should only be used in presentation layer and scripts.")
        return 1
    else:
        print("OK: No forbidden DI container imports found in guarded paths.")
        return 0


if __name__ == "__main__":
    sys.exit(main())