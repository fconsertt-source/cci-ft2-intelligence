import re
from pathlib import Path
from datetime import datetime
import pandas as pd

from src.infrastructure.registry.session_registry import SessionRegistry
from src.infrastructure.storage.parquet_repository import ParquetStorageRepository
from src.infrastructure.storage.exceptions import SessionNotFoundError


def _to_dataframe(data) -> pd.DataFrame:
    """
    تحويل آمن لأي نوع بيانات إلى DataFrame.
    يدعم: DataFrame، list، tuple، generator، iterator.
    """
    if isinstance(data, pd.DataFrame):
        return data
    # generator أو أي iterable آخر → list أولاً ثم DataFrame
    return pd.DataFrame(list(data))


class IncrementalPipelineProcessor:
    """محرك المعالجة التزايدية الآمنة - يدعم _converted.csv"""

    def __init__(self, registry: SessionRegistry, storage: ParquetStorageRepository):
        self.registry = registry
        self.storage = storage

    def extract_metadata(self, csv_path: Path) -> dict:
        """استخراج device_id من اسم الملف"""
        stem = csv_path.stem
        match = re.match(r"^(\d+)", stem)
        if not match:
            raise ValueError(f"Invalid FT2 filename format: {csv_path.name}")

        device_id = match.group(1)

        ts_match = re.search(r"_(\d{8}\d{4})", stem)
        if ts_match:
            ts_str = ts_match.group(1)
            report_dt = datetime.strptime(ts_str, "%Y%m%d%H%M")
        else:
            report_dt = datetime.fromtimestamp(csv_path.stat().st_mtime)

        return {
            "device_id": device_id,
            "report_timestamp": report_dt,
            "filename": csv_path.name,
            "full_path": str(csv_path)
        }

    def process_file(self, csv_path: Path, force: bool = False) -> dict:
        """معالجة ملف FT2 بشكل تزايدي"""
        meta = self.extract_metadata(csv_path)
        device_id = meta["device_id"]
        file_ts = meta["report_timestamp"]

        # ✅ الإصلاح: --force يتجاوز فحص SessionRegistry تماماً
        if not force and not self.registry.is_new_data(device_id, file_ts):
            return {"status": "skipped", "reason": "already_processed", **meta}

        # قراءة البيانات الجديدة
        new_df = pd.read_csv(csv_path)
        new_df = new_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")

        # قراءة البيانات السابقة
        # ✅ الإصلاح: الإمساك بـ SessionNotFoundError المخصصة من ParquetStorageRepository
        try:
            raw_existing = self.storage.read_session(device_id)
            existing_df = _to_dataframe(raw_existing)
        except (SessionNotFoundError, FileNotFoundError):
            # جلسة جديدة — لا بيانات سابقة
            existing_df = pd.DataFrame()

        # دمج آمن
        if not existing_df.empty:
            merged = pd.concat([existing_df, new_df], ignore_index=True)
            merged = merged.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
        else:
            merged = new_df

        # حفظ الجلسة — write_session يستقبل Iterator[Dict] لذا نمرر iter()
        self.storage.write_session(device_id, iter(merged.to_dict("records")))
        self.registry.mark_processed(device_id, file_ts, csv_path.name, len(new_df))

        return {
            "status": "processed",
            "device_id": device_id,
            "new_readings": len(new_df),
            "total_readings": len(merged),
            "time_range": (merged["timestamp"].min(), merged["timestamp"].max())
        }