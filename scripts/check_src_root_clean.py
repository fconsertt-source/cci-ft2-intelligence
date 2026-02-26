# scripts/check_src_root_clean.py
#!/usr/bin/env python3
"""Guard: Ensure src/ root contains ONLY the 4 layers + shared.

Allowed structure:
  src/
    domain/
    application/
    infrastructure/
    presentation/
    shared/
    __init__.py

Forbidden: Any other .py files in src/ root
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT, 'src')

ALLOWED_ITEMS = {
    'domain',
    'application', 
    'infrastructure',
    'presentation',
    'shared',
    '__init__.py',
    '__pycache__'
}

def main():
    if not os.path.exists(SRC_DIR):
        print(f"ERROR: {SRC_DIR} does not exist")
        sys.exit(1)
    
    violations = []
    items = os.listdir(SRC_DIR)
    
    for item in items:
        if item not in ALLOWED_ITEMS:
            path = os.path.join(SRC_DIR, item)
            violations.append(path)
    
    if violations:
        print("❌ ERROR: Found forbidden items in src/ root:")
        print("\n" + "="*70)
        for v in violations:
            rel = os.path.relpath(v, ROOT)
            print(f"   ⚠️  {rel}")
        print("\n" + "="*70)
        print("\n✅ ALLOWED structure:")
        print("   src/")
        print("     domain/")
        print("     application/")
        print("     infrastructure/")
        print("     presentation/")
        print("     shared/")
        print("\n📖 See: ADR-0009 (Presentation Boundary Lock)")
        sys.exit(1)
    
    print("✅ OK: src/ root is clean (4 layers + shared only)")

if __name__ == '__main__':
    main()