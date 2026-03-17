# src/application/services/device_center_mapper.py
"""
DeviceCenterMapper — خدمة الإثراء السياقي المحدَّثة.
A3: إضافة equipment_id إلى السياق المُعاد
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import yaml

from src.domain.entities.equipment_record import EquipmentRecord, EquipmentType

logger = logging.getLogger(__name__)


class DeviceCenterMapper:
    def __init__(self, mapping_file: str = "config/device_center_mapping.yaml") -> None:
        self._device_map: Dict[str, Dict] = {}
        self._equipment_map: Dict[str, Dict] = {}
        self._load_mapping(mapping_file)

    def _load_mapping(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._device_map = data.get("device_center_map", {})
            self._equipment_map = data.get("equipment_registry", {})
        except FileNotFoundError:
            logger.warning("ملف الخريطة غير موجود: %s", path)
        except Exception as e:
            logger.error("فشل تحميل خريطة الأجهزة: %s", e)

    def get_center_context(self, device_id: str) -> Optional[Dict]:
        entry = self._device_map.get(device_id)
        if not entry:
            return None
        return {
            "center_id": entry.get("center_id", "UNKNOWN"),
            "equipment_id": entry.get("equipment_id", "UNKNOWN"),
            "equipment_type": entry.get("equipment_type", "REFRIGERATOR"),
            "location_note": entry.get("location_note"),
            "status": entry.get("status", "ACTIVE"),
        }

    def get_equipment_id(self, device_id: str) -> Optional[str]:
        entry = self._device_map.get(device_id)
        return entry.get("equipment_id") if entry else None

    def get_center_id(self, device_id: str) -> Optional[str]:
        entry = self._device_map.get(device_id)
        return entry.get("center_id") if entry else None

    def get_equipment_record(self, equipment_id: str) -> Optional[EquipmentRecord]:
        entry = self._equipment_map.get(equipment_id)
        if not entry:
            for device_entry in self._device_map.values():
                if device_entry.get("equipment_id") == equipment_id:
                    return EquipmentRecord(
                        equipment_id=equipment_id,
                        center_id=device_entry.get("center_id", "UNKNOWN"),
                        equipment_type=EquipmentType(
                            device_entry.get("equipment_type", "REFRIGERATOR")
                        ),
                        location_note=device_entry.get("location_note"),
                    )
            return None
        return EquipmentRecord(
            equipment_id=equipment_id,
            center_id=entry.get("center_id", "UNKNOWN"),
            equipment_type=EquipmentType(entry.get("equipment_type", "REFRIGERATOR")),
            location_note=entry.get("location_note"),
            capacity_liters=entry.get("capacity_liters"),
        )

    def get_all_devices_for_equipment(self, equipment_id: str) -> List[str]:
        return [
            device_id
            for device_id, entry in self._device_map.items()
            if entry.get("equipment_id") == equipment_id
        ]

    def get_all_equipment_for_center(self, center_id: str) -> List[str]:
        equipment_ids = set()
        for entry in self._device_map.values():
            if entry.get("center_id") == center_id:
                eq_id = entry.get("equipment_id")
                if eq_id:
                    equipment_ids.add(eq_id)
        return sorted(equipment_ids)

    def is_mapped(self, device_id: str) -> bool:
        return device_id in self._device_map
