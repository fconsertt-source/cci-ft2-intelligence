#!/usr/bin/env python3
"""Guard script: fail if `src.core.entities` is imported in forbidden locations.

Usage: run from repo root. Returns exit code 1 on violations.
"""
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(__file__))
TARGET_DIRS = [
    os.path.join(ROOT, 'scripts'),
    os.path.join(ROOT, 'src', 'presentation')
]

# Allowlisted legacy tool directories (explicit, minimal)
ALLOWED_LEGACY = [
    os.path.join(ROOT, 'tools', 'legacy')
]

PATTERN = re.compile(r"\bfrom\s+src\.core\.entities|\bimport\s+src\.core\.entities|src\.core\.entities\.")

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
            # Skip allowed legacy trees if scanning under them
            skip_root = False
            for allowed in ALLOWED_LEGACY:
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
        print("ERROR: Found forbidden imports of src.core.entities in guarded paths:")
        for p, ln, s in violations:
            print(f" - {p}:{ln}: {s}")
        print("\nPlease convert usage to DTOs and mappers; see docs/adr/0004-phase3-plan.md")
        sys.exit(1)

    print("OK: No forbidden imports found in guarded paths.")

if __name__ == '__main__':
    main()
