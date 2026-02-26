# scripts/check_di_container_usage.py
#!/usr/bin/env python3
"""Guard: Prevent direct instantiation of Use Cases outside di_container.py

Violations:
- Importing Use Case classes in non-test files (except di_container.py)
- Direct instantiation: EvaluateColdChainSafetyUseCase()
"""
import os
import sys
import re
import ast

ROOT = os.path.dirname(os.path.dirname(__file__))

# Use Cases that MUST be created via di_container only
PROTECTED_USE_CASES = [
    "EvaluateColdChainSafetyUseCase"
]

# Allowed locations to import Use Cases
ALLOWED_IMPORTS = [
    os.path.join(ROOT, 'src', 'shared', 'di_container.py'),
    os.path.join(ROOT, 'tests'),  # Tests can import directly
]

FORBIDDEN_DIRS = [
    os.path.join(ROOT, 'src', 'presentation'),
    os.path.join(ROOT, 'src', 'infrastructure'),
]

def is_in_allowed_path(filepath):
    """Check if file is in allowed import locations."""
    for allowed in ALLOWED_IMPORTS:
        try:
            if os.path.commonpath([filepath, allowed]) == allowed:
                return True
        except ValueError:
            pass
    return False

def scan_file(path):
    """Find violations in a Python file."""
    violations = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern 1: Direct import of Use Case
        for uc in PROTECTED_USE_CASES:
            pattern = rf"from\s+src\.application\.use_cases.*import\s+{uc}|import\s+.*{uc}"
            if re.search(pattern, content):
                violations.append(f"Direct import of {uc} (must use di_container.build_evaluate_uc())")
        
        # Pattern 2: Direct instantiation
        for uc in PROTECTED_USE_CASES:
            pattern = rf"{uc}\s*\("
            if re.search(pattern, content):
                violations.append(f"Direct instantiation of {uc} (must use di_container.build_evaluate_uc())")
    
    except Exception as e:
        print(f"Warning: Could not scan {path}: {e}")
    
    return violations

def main():
    violations_found = []
    
    for forbidden_dir in FORBIDDEN_DIRS:
        if not os.path.exists(forbidden_dir):
            continue
        
        for root, _, files in os.walk(forbidden_dir):
            for fn in files:
                if not fn.endswith('.py'):
                    continue
                
                filepath = os.path.join(root, fn)
                
                # Skip if in allowed path
                if is_in_allowed_path(filepath):
                    continue
                
                violations = scan_file(filepath)
                if violations:
                    for v in violations:
                        violations_found.append((filepath, v))
    
    if violations_found:
        print("❌ ERROR: Found DI Container violations:")
        print("\n" + "="*70)
        for path, msg in violations_found:
            rel_path = os.path.relpath(path, ROOT)
            print(f"\n📁 {rel_path}")
            print(f"   ⚠️  {msg}")
        print("\n" + "="*70)
        print("\n✅ SOLUTION: Use di_container.build_evaluate_uc() instead")
        print("   Example:")
        print("   from src.shared.di_container import build_evaluate_uc")
        print("   uc = build_evaluate_uc()")
        print("\n📖 See: docs/adr/0009-presentation-boundary-lock.md")
        sys.exit(1)
    
    print("✅ OK: All Use Cases created via DI Container")

if __name__ == '__main__':
    main()