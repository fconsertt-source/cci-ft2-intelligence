#!/usr/bin/env python3
"""Wrapper script for project migration utilities."""

from scripts.migrate_domain_dtos import migrate


if __name__ == "__main__":
    success = migrate()
    if not success:
        raise SystemExit(1)
