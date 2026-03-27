#!/usr/bin/env python3
import ast
from pathlib import Path
import pytest

APP_PATH = Path("src/application")
FORBIDDEN_IMPORTS = ["infrastructure", "django", "sqlalchemy"]

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

def test_application_does_not_import_infrastructure():
    failed = []
    for py_file in APP_PATH.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        for imp in get_imports(py_file):
            if imp in FORBIDDEN_IMPORTS:
                failed.append(f"{py_file} يستورد {imp}")
    assert not failed, "\n".join(failed)