#!/usr/bin/env python3
"""
معالجة ملفات FT2: تحقق رقمي → استخراج بيانات → تحويل CSV → أرشفة → Ledger

Data Flow:
    data/input_ft2/incoming/*.txt → Verify → Extract → Archive → data/input_raw/*.csv
    مع تسجيل كل خطوة في Ledger للتدقيق الجنائي
"""

import csv
import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# إضافة جذر المشروع للمسار
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.domain.enums.ledger_event import LedgerEvent
from src.shared.di_container import configure_ledger, container

# تهيئة التسجيل
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """حساب بصمة SHA-256 للملف"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_ft2_data(input_path: Path) -> dict:
    """
    استخراج البيانات من ملف FT2.

    TODO: استبدل هذا بالمنطق الفعلي لاستخراج بيانات FT2
    """
    # استخراج device_id من اسم الملف
    # مثال: 130600112764_202201241939.txt → device_id = 130600112764
    device_id = input_path.stem.split("_")[0] if "_" in input_path.stem else "unknown"

    return {
        "device_id": device_id,
        "timestamp": input_path.stem.split("_")[1] if "_" in input_path.stem else "",
        "file_hash": calculate_sha256(input_path),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(input_path),
    }


def convert_to_csv(data: dict, output_path: Path) -> None:
    """تحويل البيانات المستخرجة إلى CSV"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)


def archive_file(source_path: Path, device_id: str, archive_root: Path) -> Path:
    """
    أرشفة الملف الأصلي في مسار منظم.

    المسار: archive/YYYY/MM/device_{id}/timestamp_deviceID.ext
    """
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    archive_dir = archive_root / year / month / f"device_{device_id}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_path = archive_dir / f"{timestamp}_{device_id}{source_path.suffix}"

    # نقل ذري (نفس filesystem)
    source_path.rename(archive_path)

    return archive_path


def process_single_file(
    file_path: Path, ledger: LedgerWriterPort, archive_root: Path, csv_output_dir: Path
) -> bool:
    """
    معالجة ملف FT2 واحد: تحقق → استخراج → CSV → أرشفة → Ledger

    Returns:
        bool: True إذا نجحت المعالجة، False إذا فشلت
    """
    event_id = None

    try:
        logger.info(f"Processing: {file_path.name}")

        # 1. استخراج device_id
        device_id = file_path.stem.split("_")[0] if "_" in file_path.stem else "unknown"
        logger.debug(f"  Device ID: {device_id}")

        # 2. حساب البصمة قبل المعالجة
        file_hash = calculate_sha256(file_path)
        logger.debug(f"  SHA-256: {file_hash[:16]}...")

        # 3. تسجيل حدث FILE_INGESTED في Ledger
        event_id = f"ft2-ingest-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{file_path.stem}"
        ledger.append(
            event_type=LedgerEvent.FILE_INGESTED,
            file_hash=file_hash,
            event_id=event_id,
            ft2_serial=device_id,
            source_path=str(file_path),
        )
        logger.debug("  Logged: FILE_INGESTED")

        # 4. استخراج البيانات
        data = extract_ft2_data(file_path)

        # 5. تحويل إلى CSV
        output_name = f"{file_path.stem}_processed.csv"
        output_path = csv_output_dir / output_name
        convert_to_csv(data, output_path)
        logger.debug(f"  CSV: {output_path.name}")

        # 6. تسجيل حدث FILE_VALIDATED
        ledger.append(
            event_type=LedgerEvent.FILE_VALIDATED,
            file_hash=file_hash,
            event_id=f"{event_id}-validated",
            ft2_serial=device_id,
            destination_path=str(output_path),
        )

        # 7. أرشفة الملف الأصلي
        archive_path = archive_file(file_path, device_id, archive_root)
        logger.debug(f"  Archived: {archive_path.name}")

        # 8. التحقق من سلامة الأرشفة (hash بعد النقل)
        archived_hash = calculate_sha256(archive_path)
        if archived_hash != file_hash:
            raise RuntimeError(
                f"Hash mismatch after archival: {file_hash} != {archived_hash}"
            )

        # 9. تسجيل حدث FILE_ARCHIVED
        ledger.append(
            event_type=LedgerEvent.FILE_ARCHIVED,
            file_hash=file_hash,
            event_id=f"{event_id}-archived",
            ft2_serial=device_id,
            source_path=str(file_path),
            destination_path=str(archive_path),
        )
        logger.debug("  Logged: FILE_ARCHIVED")

        logger.info(f"  ✅ Success: {file_path.name}")
        return True

    except Exception as e:
        logger.error(f"  ❌ Failed: {file_path.name} - {e}")

        # تسجيل الفشل في Ledger إذا أمكن
        if event_id and ledger:
            try:
                ledger.append(
                    event_type=LedgerEvent.FILE_CORRUPTED,
                    file_hash=file_hash if "file_hash" in locals() else "UNKNOWN",
                    event_id=f"{event_id}-failed",
                    ft2_serial=device_id if "device_id" in locals() else "unknown",
                    metadata={"error": str(e)},
                )
            except Exception:
                pass  # لا نفشل مرتين

        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python -m scripts.process_ft2 <file_or_directory>")
        print("\n📁 Examples:")
        print("   python -m scripts.process_ft2 data/input_ft2/incoming/")
        print("   python -m scripts.process_ft2 data/input_ft2/incoming/device_123.txt")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # تهيئة المسارات
    project_root = Path(__file__).parent.parent
    archive_root = project_root / "data" / "archive"
    csv_output_dir = project_root / "data" / "input_raw" / "processed"
    ledger_path = project_root / "data" / "ledger" / "verification_ledger.jsonl"

    # تهيئة Ledger
    logger.info(f"Initializing Ledger: {ledger_path}")
    ledger = configure_ledger(ledger_path)

    # جمع الملفات للمعالجة
    if input_path.is_dir():
        files = list(input_path.glob("*.txt")) + list(input_path.glob("*.pdf"))
    else:
        files = [input_path] if input_path.exists() else []

    if not files:
        logger.error(f"No FT2 files found in: {input_path}")
        sys.exit(1)

    logger.info(f"Processing {len(files)} FT2 file(s)...")
    logger.info(f"Archive Root: {archive_root}")
    logger.info(f"CSV Output: {csv_output_dir}")
    logger.info(f"{'='*60}")

    # معالجة كل ملف
    processed_count = 0
    failed_count = 0

    for file_path in files:
        if process_single_file(file_path, ledger, archive_root, csv_output_dir):
            processed_count += 1
        else:
            failed_count += 1

    # الملخص
    logger.info(f"\n{'='*60}")
    logger.info("📊 Processing Summary")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Processed: {processed_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"📁 CSV Output: {csv_output_dir}")
    logger.info(f"🗄️  Archive: {archive_root}")
    logger.info(f"📜 Ledger: {ledger_path}")
    logger.info(f"{'='*60}")

    # عرض حالة السلسلة
    state = ledger.get_chain_state()
    logger.info(
        f"Ledger State: {state.entry_count} entries, last_hash={state.last_entry_hash[:16] if state.last_entry_hash else 'None'}..."
    )

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
