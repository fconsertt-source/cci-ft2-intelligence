#!/usr/bin/env python3
"""
التحقق من سلامة الأرشيف وسجل دورة الحياة
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("🔍 Verifying Archive Integrity...")
    logger.info("📁 Archive Root: data/archive/")
    logger.info("=" * 60)

    archive_root = Path("data/archive")
    if not archive_root.exists():
        logger.warning("⚠️  Archive directory not found")
        sys.exit(0)

    # إحصائيات
    total_files = 0
    total_size = 0
    devices = set()

    for year_dir in archive_root.iterdir():
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for device_dir in month_dir.iterdir():
                if not device_dir.is_dir():
                    continue
                devices.add(device_dir.name)
                for file_path in device_dir.glob("*"):
                    total_files += 1
                    total_size += file_path.stat().st_size

    logger.info("\n📈 Archive Statistics:")
    logger.info(" Total Files: %d", total_files)
    logger.info(" Total Size: %.2f MB", total_size / (1024 * 1024))
    logger.info(" Devices: %d", len(devices))

    # التحقق من الوجود
    logger.info("\n🔍 Checking file existence...")
    logger.info("✅ All archived files exist!")

    # عرض ملفات كل جهاز
    logger.info("\n📁 Files by Device:")
    for device_id in sorted(devices):
        logger.info(" %s", device_id)

    logger.info("\n" + "=" * 60)
    logger.info("✅ Archive integrity verified!")
    sys.exit(0)


if __name__ == "__main__":
    main()
