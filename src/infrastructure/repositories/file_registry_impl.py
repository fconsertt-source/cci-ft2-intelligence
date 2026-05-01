import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.application.ports.i_file_registry import IFileRegistry
from src.shared.utils.time_utils import utc_now_datetime

logger = logging.getLogger(__name__)

class FileRegistryImpl(IFileRegistry):
    """
    Infrastructure: تنفيذ سجل الملفات كـ JSON.

    يُخزّن في data/registry/processed_files.json
    يضمن Idempotency: الملف المعالَج لا يُعالَج مجدداً.
    يدعم Rollback: يسجّل run_id لكل ملف.
    """

    MAX_JSON_ENTRIES = 10_000  # حد أمان قبل الترحيل لـ SQLite

    def __init__(self, registry_path: Path):
        self._path = registry_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    def is_processed(self, file_hash: str) -> bool:
        return file_hash in self._data.get("processed", {})

    def mark_processed(
        self,
        file_hash: str,
        device_id: str,
        run_id: str,
        processed_at: datetime
    ) -> None:
        if "processed" not in self._data:
            self._data["processed"] = {}

        self._data["processed"][file_hash] = {
            "device_id": device_id,
            "run_id": run_id,
            "processed_at": processed_at.isoformat()
        }

        if len(self._data["processed"]) > self.MAX_JSON_ENTRIES:
            logger.warning(
                "Registry يقترب من الحد الأقصى (%d). فكّر في الترحيل لـ SQLite",
                self.MAX_JSON_ENTRIES
            )

        self._save()

    def mark_quarantined(self, file_hash: str, reason_ar: str, reason_en: str) -> None:
        if "quarantined" not in self._data:
            self._data["quarantined"] = {}

        self._data["quarantined"][file_hash] = {
            "reason_ar": reason_ar,
            "reason_en": reason_en,
            "quarantined_at": utc_now_datetime().isoformat()
        }
        self._save()

    def get_run_files(self, run_id: str) -> list[str]:
        """للـ Rollback: جلب كل ملفات تشغيل محدد"""
        return [hash_val for hash_val, info in self._data.get("processed", {}).items() if info.get("run_id") == run_id]

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.error("Registry تالف — بدء من صفر")
                return {}
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")