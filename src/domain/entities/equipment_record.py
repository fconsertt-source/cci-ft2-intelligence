# src/domain/entities/equipment_record.py
"""
EquipmentRecord — معدة التبريد الفيزيائية.

الطبقة الوسطى بين:
  device_id (جهاز FT2) ← equipment_id → center_id (مركز التطعيم)

لماذا هذه الطبقة ضرورية؟
  - مركز واحد قد يحتوي أكثر من معدة (ثلاجة + غرفة تبريد)
  - كل معدة لها سجل حراري مستقل
  - اللقاحات ترتبط بالمعدة وليس بالجهاز أو المركز مباشرة
  - عند استبدال الجهاز تبقى المعدة ثابتة والسلسلة متصلة
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EquipmentType(Enum):
    """نوع معدة التبريد."""

    REFRIGERATOR = "REFRIGERATOR"  # ثلاجة عادية (+2 إلى +8°C)
    COLD_ROOM = "COLD_ROOM"  # غرفة تبريد (+2 إلى +8°C)
    FREEZER = "FREEZER"  # فريزر (-15 إلى -25°C)
    DEEP_FREEZER = "DEEP_FREEZER"  # فريزر عميق (< -25°C)
    TRANSPORT_BOX = "TRANSPORT_BOX"  # صندوق نقل مؤقت


@dataclass(frozen=True)
class EquipmentRecord:
    """
    سجل معدة التبريد — Immutable.

    Attributes:
        equipment_id:    معرف فريد للمعدة (مثال: EQ-FRIDGE-01)
        center_id:       معرف المركز الذي تنتمي إليه
        equipment_type:  نوع المعدة
        location_note:   وصف موقع المعدة داخل المركز (اختياري)
        active_device_id: معرف الجهاز النشط حالياً على هذه المعدة
        capacity_liters: سعة المعدة بالليتر (وصفي فقط)
    """

    equipment_id: str
    center_id: str
    equipment_type: EquipmentType = EquipmentType.REFRIGERATOR
    location_note: Optional[str] = None
    active_device_id: Optional[str] = None
    capacity_liters: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.equipment_id or not self.equipment_id.strip():
            raise ValueError("equipment_id cannot be empty")
        if not self.center_id or not self.center_id.strip():
            raise ValueError("center_id cannot be empty")

    def with_active_device(self, device_id: str) -> "EquipmentRecord":
        """إرجاع نسخة جديدة مع تحديث الجهاز النشط."""
        return EquipmentRecord(
            equipment_id=self.equipment_id,
            center_id=self.center_id,
            equipment_type=self.equipment_type,
            location_note=self.location_note,
            active_device_id=device_id,
            capacity_liters=self.capacity_liters,
        )

    def to_dict(self) -> dict:
        return {
            "equipment_id": self.equipment_id,
            "center_id": self.center_id,
            "equipment_type": self.equipment_type.value,
            "location_note": self.location_note,
            "active_device_id": self.active_device_id,
            "capacity_liters": self.capacity_liters,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentRecord":
        return cls(
            equipment_id=data["equipment_id"],
            center_id=data["center_id"],
            equipment_type=EquipmentType(data.get("equipment_type", "REFRIGERATOR")),
            location_note=data.get("location_note"),
            active_device_id=data.get("active_device_id"),
            capacity_liters=data.get("capacity_liters"),
        )

    def __str__(self) -> str:
        return (
            f"EquipmentRecord [{self.equipment_id}] "
            f"نوع={self.equipment_type.value} "
            f"مركز={self.center_id} "
            f"جهاز={self.active_device_id or 'غير مربوط'}"
        )
