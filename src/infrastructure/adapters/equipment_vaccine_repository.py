# src/infrastructure/adapters/equipment_vaccine_repository.py
"""
EquipmentVaccineRepository — تخزين واسترجاع بيانات اللقاحات في المعدات.

التخزين: data/equipment_vaccines.json
القراءة: حسب equipment_id أو center_id
الكتابة: إضافة/تحديث/حذف دفعة لقاح
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.domain.entities.equipment_vaccine import EquipmentVaccine

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path("data/equipment_vaccines.json")


class EquipmentVaccineRepository:
    """
    مستودع بيانات اللقاحات في المعدات.

    يُحمِّل البيانات من JSON ويحفظها عند كل تغيير.
    """

    def __init__(self, data_path: Path = _DEFAULT_PATH) -> None:
        self._path = Path(data_path)
        self._vaccines: List[EquipmentVaccine] = self._load()

    # ──────────────────────────────────────────────────────────
    # استعلامات
    # ──────────────────────────────────────────────────────────

    def get_by_equipment(self, equipment_id: str) -> List[EquipmentVaccine]:
        """جلب جميع اللقاحات في معدة معينة."""
        return [v for v in self._vaccines if v.equipment_id == equipment_id]

    def get_by_center(self, center_id: str) -> List[EquipmentVaccine]:
        """جلب جميع اللقاحات في مركز معين."""
        return [v for v in self._vaccines if v.center_id == center_id]

    def get_by_entry_id(self, entry_id: str) -> Optional[EquipmentVaccine]:
        """جلب دفعة لقاح بمعرفها."""
        for v in self._vaccines:
            if v.entry_id == entry_id:
                return v
        return None

    def get_expired(self) -> List[EquipmentVaccine]:
        """جلب اللقاحات المنتهية الصلاحية."""
        return [v for v in self._vaccines if v.is_expired]

    def get_active(self, equipment_id: str) -> List[EquipmentVaccine]:
        """جلب اللقاحات الصالحة (غير منتهية) في معدة معينة."""
        return [v for v in self.get_by_equipment(equipment_id) if not v.is_expired]

    # ──────────────────────────────────────────────────────────
    # عمليات الكتابة
    # ──────────────────────────────────────────────────────────

    def add(self, vaccine: EquipmentVaccine) -> None:
        """إضافة دفعة لقاح جديدة."""
        self._vaccines.append(vaccine)
        self._save()
        logger.info(
            "تمت إضافة لقاح: %s دفعة=%s معدة=%s",
            vaccine.vaccine_type,
            vaccine.batch_number,
            vaccine.equipment_id,
        )

    def remove(self, entry_id: str) -> bool:
        """حذف دفعة لقاح بمعرفها. يعيد True إذا نجح الحذف."""
        before = len(self._vaccines)
        self._vaccines = [v for v in self._vaccines if v.entry_id != entry_id]
        if len(self._vaccines) < before:
            self._save()
            logger.info("تم حذف اللقاح: %s", entry_id)
            return True
        return False

    def update_vvm_stage(
        self,
        entry_id: str,
        new_stage,
    ) -> Optional[EquipmentVaccine]:
        """
        تحديث مرحلة VVM للقاح معين.
        يعيد النسخة المحدَّثة أو None إذا لم يُوجد.
        """
        from src.domain.entities.equipment_vaccine import (EquipmentVaccine,
                                                           VVMStageValue)

        updated = []
        result = None

        for v in self._vaccines:
            if v.entry_id == entry_id:
                new_v = EquipmentVaccine(
                    entry_id=v.entry_id,
                    equipment_id=v.equipment_id,
                    center_id=v.center_id,
                    vaccine_type=v.vaccine_type,
                    batch_number=v.batch_number,
                    expiry_date=v.expiry_date,
                    quantity_doses=v.quantity_doses,
                    has_vvm=v.has_vvm,
                    vvm_stage=VVMStageValue(new_stage) if new_stage else None,
                    notes=v.notes,
                    recorded_by=v.recorded_by,
                    recorded_at=v.recorded_at,
                )
                updated.append(new_v)
                result = new_v
            else:
                updated.append(v)

        if result:
            self._vaccines = updated
            self._save()

        return result

    # ──────────────────────────────────────────────────────────
    # التخزين
    # ──────────────────────────────────────────────────────────

    def _load(self) -> List[EquipmentVaccine]:
        if not self._path.exists():
            logger.info("ملف اللقاحات غير موجود: %s — يبدأ فارغاً", self._path)
            return []
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)

            vaccines = []
            for eq_entry in data.get("equipment_vaccines", []):
                equipment_id = eq_entry["equipment_id"]
                center_id = eq_entry.get("center_id", "UNKNOWN")
                for v_data in eq_entry.get("vaccines", []):
                    v_data["equipment_id"] = equipment_id
                    v_data["center_id"] = center_id
                    vaccines.append(EquipmentVaccine.from_dict(v_data))

            logger.info("تم تحميل %d دفعة لقاح", len(vaccines))
            return vaccines

        except Exception as e:
            logger.error("فشل تحميل equipment_vaccines.json: %s", e)
            return []

    def _save(self) -> None:
        """حفظ البيانات بتجميع اللقاحات حسب equipment_id."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # تجميع حسب equipment_id
        by_equipment: Dict[str, dict] = {}
        for v in self._vaccines:
            if v.equipment_id not in by_equipment:
                by_equipment[v.equipment_id] = {
                    "equipment_id": v.equipment_id,
                    "center_id": v.center_id,
                    "vaccines": [],
                }
            by_equipment[v.equipment_id]["vaccines"].append(v.to_dict())

        output = {
            "_metadata": {
                "description": "محتويات معدات التبريد",
                "version": "1.0.0",
            },
            "equipment_vaccines": list(by_equipment.values()),
        }

        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
