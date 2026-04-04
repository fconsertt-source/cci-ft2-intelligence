from pathlib import Path
from typing import List
import logging
import json

logger = logging.getLogger(__name__)

DATA_STRUCTURE = {
    "input_ft2":       "ملفات FT2 الواردة الأصلية",
    "input_raw":       "CSV جاهز للمعالجة (ينظّف بعد كل تشغيل)",
    "staging/quarantine": "ملفات مرفوضة",
    "archive":         "ملفات معالجة موثّقة زمنياً",
    "registry":        "سجلات النظام (JSON)",
    "output":          "التقارير النهائية",
}

class CSVLifecycleManager:
    """
    Infrastructure: إدارة دورة حياة ملفات CSV في المجلدات.
    """

    def __init__(self, base_data_path: Path):
        self._base = base_data_path

    def ensure_structure(self) -> None:
        """يتحقق من هيكل المجلدات ويُنشئ المفقودة."""
        for dir_name in DATA_STRUCTURE:
            target = self._base / dir_name
            target.mkdir(parents=True, exist_ok=True)

        logger.info("هيكل المجلدات مُتحقق منه / Directory structure verified")

    def get_input_raw_files(self) -> List[Path]:
        """جلب ملفات CSV الجاهزة للمعالجة."""
        input_raw = self._base / "input_raw"
        files = list(input_raw.glob("*.csv"))
        logger.info(f"وجد {len(files)} ملف للمعالجة في input_raw / Found {len(files)} files in input_raw")
        return files

    def count_registry_entries(self) -> int:
        """عدد الملفات المسجلة (للـ Observability)."""
        registry = self._base / "registry" / "processed_files.json"
        if not registry.exists():
            return 0
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            return len(data.get("processed", {}))
        except Exception:
            return 0