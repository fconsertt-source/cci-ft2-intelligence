# src/infrastructure/adapters/json_vaccine_repository.py
import json
from pathlib import Path
from typing import Optional

from src.application.ports.vaccine_repository_port import VaccineRepositoryPort
from src.domain.entities.vaccine_batch import VaccineBatch


class JsonVaccineRepository(VaccineRepositoryPort):
    """Simple JSON-based persistence — ideal for field deployment."""

    def __init__(self, storage_path: str = "data/batches"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_batch(self, batch: VaccineBatch) -> None:
        # ← حفظ إلى ملف منفصل لكل دفعة
        #    مثال: data/batches/OPV-2024-01.json
        file_path = self.storage_path / f"{batch.batch_id}.json"

        # ← هيكل بسيط يحتوي على:
        #    • بيانات الدفعة الأساسية
        #    • سجل التعرض التراكمي (قائمة من المراحل)
        #    • الطابع الزمني للتحديث الأخير
        data = {
            "batch_id": batch.batch_id,
            "vaccine_type": batch.vaccine_type.value,
            "manufacture_date": batch.manufacture_date.isoformat(),
            "exposure_history": [
                {
                    "stage": exp.stage,
                    "device_id": exp.device_id,
                    "her": exp.her,
                    "ccm": exp.ccm,
                    "timestamp": exp.timestamp.isoformat(),
                }
                for exp in batch.exposure_history
            ],
            "last_updated": batch.last_updated.isoformat(),
            "cumulative_her": batch.cumulative_her,
            "cumulative_ccm": batch.cumulative_ccm,
            "status": batch.status.value,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_batch(self, batch_id: str) -> Optional[VaccineBatch]:
        file_path = self.storage_path / f"{batch_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # ← إعادة بناء كائن VaccineBatch من البيانات
            return VaccineBatch.from_dict(data)
