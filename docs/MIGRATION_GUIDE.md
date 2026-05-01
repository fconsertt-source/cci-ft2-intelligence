# Migration Guide

This guide describes the migration utilities and procedures available in the project.

## Migration entry point

- `scripts/migrate.py` - wrapper entrypoint for migration workflows.

## Migration modules

- `scripts/migrate_domain_dtos.py` - contains the `migrate()` function used by the migration wrapper.

## Usage

Run the migration wrapper from the repository root:

```bash
python3 scripts/migrate.py
```

## Notes

- This project separates migration utilities from backup utilities.
- The migration wrapper should only orchestrate domain migration steps.
