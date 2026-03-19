#!/usr/bin/env python3
"""
اختبارات التأكد من أن طبقة Domain لا تعتمد على أي طبقة خارجية.
"""
import ast
from pathlib import Path

DOMAIN_PATH = Path("src/domain")
FORBIDDEN_IMPORTS = [
    "infrastructure",
    "presentation",
    "application",
    "django",
    "sqlalchemy",
]


def get_imports(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def test_domain_does_not_import_forbidden_layers():
    failed = []
    for py_file in DOMAIN_PATH.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        for imp in get_imports(py_file):
            if imp in FORBIDDEN_IMPORTS:
                failed.append(f"{py_file} يستورد {imp}")
    assert not failed, "\n".join(failed)
