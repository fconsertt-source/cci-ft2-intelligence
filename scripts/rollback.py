#!/usr/bin/env python3
"""
Rollback Utility - سكربت التراجع عن التحديثات الفاشلة

Restores data from the most recent backup.
Guardrail (Engineer): Raises if no backup exists — never silently succeeds.
"""

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("backups")
DATA_DIR = Path("data")


def _find_latest_backup() -> Path | None:
    """Find the most recent backup directory by modification time."""
    if not BACKUP_DIR.exists():
        return None
    backups = sorted(
        BACKUP_DIR.iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for backup in backups:
        if backup.is_dir() and any(backup.iterdir()):
            return backup
    return None


def _verify_backup(backup_path: Path) -> bool:
    """Verify backup contains expected data files."""
    expected = (backup_path / "archive", backup_path / "input_ft2",
                backup_path / "ledger")
    return any(p.exists() and any(p.iterdir()) for p in expected)


def create_backup() -> Path:
    """Create a timestamped backup of current data before any mutation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"pre_rollback_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for sub in DATA_DIR.iterdir():
            if sub.is_dir():
                shutil.copytree(sub, backup_path / sub.name, dirs_exist_ok=True)
            else:
                shutil.copy2(sub, backup_path / sub.name)

    logger.info("Backup created at %s", backup_path)
    return backup_path


def restore_backup() -> bool:
    """
    Restore data from the latest backup.

    Guardrail: Raises RuntimeError if no valid backup is found.
    """
    backup_path = _find_latest_backup()

    if backup_path is None:
        raise RuntimeError(
            "CRITICAL: No backup found. Refusing to proceed with rollback "
            "without a restore point. Create a backup first."
        )

    if not _verify_backup(backup_path):
        raise RuntimeError(
            f"CRITICAL: Backup at {backup_path} appears incomplete or empty. "
            "Refusing to restore from corrupted backup."
        )

    logger.info("Restoring data from backup: %s", backup_path)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for item in backup_path.iterdir():
        dest = DATA_DIR / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    logger.info("Rollback complete — restored from %s", backup_path.name)
    return True


def execute_rollback() -> bool:
    """Main rollback function — creates pre-rollback backup, then restores."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Initializing rollback procedure...")

    # Snapshot current state before restoring (safety net)
    try:
        create_backup()
    except Exception as e:
        logger.warning("Could not create pre-rollback snapshot: %s", e)

    try:
        success = restore_backup()
        logger.info("Rollback complete.")
        return success
    except RuntimeError:
        raise
    except Exception as e:
        logger.error("Rollback failed: %s", e)
        return False


def perform_rollback() -> bool:
    """Alias for execute_rollback."""
    return execute_rollback()


def main():
    """Entry point."""
    try:
        if not execute_rollback():
            sys.exit(1)
    except RuntimeError as e:
        logger.critical("Rollback aborted: %s", e)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
