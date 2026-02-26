#!/usr/bin/env python3
"""
تنظيف الملفات المنتهية الصلاحية (>90 يوم) من الأرشيف
يُشغل يومياً عبر cron:
0 2 * * * cd /path/to/project && python -m scripts.cleanup_archive.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.di_container import container, configure_ledger
from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.domain.ledger.events import LedgerEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    dry_run = '--dry-run' in sys.argv
    
    logger.info("🗑️  Archive Cleanup Utility")
    logger.info(f"📁 Archive Root: data/archive/")
    logger.info(f"⏰ Retention: 90 days")
    logger.info(f"🔍 Mode: {'DRY RUN (no deletion)' if dry_run else 'LIVE (will delete)'}")
    logger.info("="*60)
    
    # ملاحظة: في النسخة الحالية، التنظيف اليدوي يتم عبر فحص المجلدات
    # يمكن تطويره لاحقاً مع FileLifecycleManager
    
    archive_root = Path('data/archive')
    if not archive_root.exists():
        logger.info("✅ No archive found")
        sys.exit(0)
    
    # فحص الملفات حسب التاريخ
    cutoff = datetime.now(timezone.utc).timestamp() - (90 * 24 * 60 * 60)
    expired_count = 0
    
    for year_dir in archive_root.iterdir():
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for device_dir in month_dir.iterdir():
                if not device_dir.is_dir():
                    continue
                for file_path in device_dir.glob('*'):
                    if file_path.stat().st_mtime < cutoff:
                        expired_count += 1
                        if dry_run:
                            logger.info(f"🔍 Would delete: {file_path}")
                        else:
                            logger.info(f"🗑️  Deleting: {file_path}")
                            file_path.unlink()
    
    logger.info("="*60)
    logger.info(f"📊 Cleanup Results:")
    logger.info(f"   Expired files found: {expired_count}")
    if dry_run:
        logger.info("   (DRY RUN - no files deleted)")
    else:
        logger.info(f"   Files deleted: {expired_count}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
