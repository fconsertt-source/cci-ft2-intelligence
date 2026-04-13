"""
migrate_pickle_to_parquet.py
-----------------------------
هجرة آمنة من ملفات Pickle إلى Parquet.

الاستخدام:
    # مرحلة التحليل فقط (لا كتابة):
    python migrate_pickle_to_parquet.py --source ./data/pkl --target ./data/parquet --dry-run

    # هجرة فعلية:
    python migrate_pickle_to_parquet.py --source ./data/pkl --target ./data/parquet

    # هجرة مع حساب checksum (أبطأ لكن أكثر أماناً):
    python migrate_pickle_to_parquet.py --source ./data/pkl --target ./data/parquet --strict-checksum

تحذير:
    Pickle يُشغِّل كوداً عند التحميل. تأكد من أن المصدر موثوق.
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Any

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _load_pickle(path: Path) -> Any:
    """يحمّل ملف pickle ويتحقق من أنه list أو DataFrame."""
    with open(path, "rb") as f:
        data = pickle.load(f)  # noqa: S301 - المصدر موثوق داخلياً

    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, (list, dict)):
        return pd.DataFrame(data)

    raise TypeError(
        f"Unsupported pickle content type: {type(data).__name__}. "
        "Expected DataFrame, list, or dict."
    )


def _verify_parquet(path: Path, expected_rows: int) -> bool:
    """تحقق سريع: يقرأ رأس الملف ويتحقق من عدد الصفوف."""
    try:
        import pyarrow.parquet as pq
        meta = pq.read_metadata(path)
        actual_rows = meta.num_rows
        if actual_rows != expected_rows:
            log.warning(
                "Row count mismatch for %s: expected %d, got %d",
                path.name, expected_rows, actual_rows,
            )
            return False
        return True
    except Exception as exc:
        log.warning("Parquet verification failed for %s: %s", path.name, exc)
        return False


def migrate(
    source_dir: Path,
    target_dir: Path,
    dry_run: bool = False,
    strict_checksum: bool = False,
) -> dict:
    """
    ينفّذ الهجرة ويعيد تقريراً بالنتائج.

    Returns:
        {"success": [...], "failed": [...], "skipped": [...]}
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"success": [], "failed": [], "skipped": []}

    pkl_files = sorted(source_dir.glob("*.pkl"))
    if not pkl_files:
        log.warning("No .pkl files found in %s", source_dir)
        return report

    log.info("Found %d .pkl files. dry_run=%s", len(pkl_files), dry_run)

    for pkl_path in pkl_files:
        target_path = target_dir / f"{pkl_path.stem}.parquet"

        # التخطي إذا كان الملف موجوداً مسبقاً
        if target_path.exists() and not dry_run:
            log.info("SKIP (already exists): %s", pkl_path.name)
            report["skipped"].append(pkl_path.name)
            continue

        if dry_run:
            log.info("DRY-RUN: would migrate %s → %s", pkl_path.name, target_path.name)
            report["skipped"].append(pkl_path.name)
            continue

        try:
            df = _load_pickle(pkl_path)
            rows = len(df)

            df.to_parquet(
                target_path,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )

            if not _verify_parquet(target_path, rows):
                raise ValueError("Post-write verification failed")

            if strict_checksum:
                import hashlib
                h = hashlib.sha256()
                with open(target_path, "rb") as f:
                    for block in iter(lambda: f.read(65_536), b""):
                        h.update(block)
                checksum = h.hexdigest()
            else:
                checksum = None

            # حفظ metadata مرافق
            meta = {
                "source_file": pkl_path.name,
                "rows": rows,
                "columns": list(df.columns),
                "checksum": checksum,
            }
            (target_dir / f"{pkl_path.stem}.meta.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            log.info("OK  %s  (%d rows)", pkl_path.name, rows)
            report["success"].append(pkl_path.name)

        except Exception as exc:
            log.error("FAIL %s: %s", pkl_path.name, exc)
            # تنظيف الملف الناقص
            target_path.unlink(missing_ok=True)
            report["failed"].append({"file": pkl_path.name, "error": str(exc)})

    # ملخص نهائي
    log.info(
        "Done → success: %d | failed: %d | skipped: %d",
        len(report["success"]),
        len(report["failed"]),
        len(report["skipped"]),
    )

    if report["failed"]:
        log.error("Failed files: %s", [f["file"] for f in report["failed"]])

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate Pickle files to Parquet format."
    )
    parser.add_argument(
        "--source", type=Path, required=True,
        help="مجلد ملفات .pkl المصدر"
    )
    parser.add_argument(
        "--target", type=Path, required=True,
        help="مجلد الإخراج لملفات .parquet"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="تحليل فقط بدون كتابة أي ملفات"
    )
    parser.add_argument(
        "--strict-checksum", action="store_true",
        help="حساب SHA-256 بعد كل كتابة (أبطأ)"
    )
    args = parser.parse_args()

    report = migrate(
        source_dir=args.source,
        target_dir=args.target,
        dry_run=args.dry_run,
        strict_checksum=args.strict_checksum,
    )

    if report["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()