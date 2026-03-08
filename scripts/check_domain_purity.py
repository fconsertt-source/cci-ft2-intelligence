#!/usr/bin/env python3
"""Verify that no code imports from `src.application.dtos` anymore.

This is a lightweight script used after DTO migration to ensure the package is
unused, supporting the decision to delete it later.

Usage:
    python3 scripts/check_domain_purity.py

Exits with status 0 if clean, 1 if any offending import is found.
"""
import subprocess
import sys

# Use grep via shell for simplicity
result = subprocess.run(
    [
        "grep",
        "-R",
        "src.application.dtos",
        "src",
        "tests",
        "tools/legacy",
    ],
    capture_output=True,
    text=True,
)

if result.returncode == 0 and result.stdout:
    print("Found references to src.application.dtos:")
    print(result.stdout)
    sys.exit(1)

print("No remaining imports from src.application.dtos found.")
sys.exit(0)
