# scripts/check_layer_dependencies.py (جديد)
"""التحقق من عدم وجود تبعيات عكسية (من الداخل إلى الخارج)"""
import ast
from pathlib import Path

VIOLATIONS = []

for py_file in Path("src/application").rglob("*.py"):
    content = py_file.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("src.presentation"):
                VIOLATIONS.append(f"{py_file}: imports from presentation layer")

if VIOLATIONS:
    print("❌ Dependency Rule Violations:")
    for v in VIOLATIONS:
        print(f"   {v}")
    exit(1)
else:
    print("✅ No reverse dependencies found")
