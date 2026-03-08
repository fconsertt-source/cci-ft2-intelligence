#!/usr/bin/env python3
"""
هوية الجهاز - عقد موحد لجميع مكونات النظام
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeviceIdentity:
    """
    هوية فريدة وموحدة لكل جهاز تبريد في النظام.

    Attributes:
        device_id: المعرف الفريد للجهاز (مثال: FT2-001)
        serial_number: الرقم التسلسلي للشركة المصنعة
        center_id: معرف مركز التبريد (اختياري عند الإنشاء)
    """

    device_id: str
    serial_number: str
    center_id: Optional[str] = None

    def __post_init__(self):
        """التحقق من صحة الهوية"""
        if not self.device_id or not self.device_id.strip():
            raise ValueError("device_id cannot be empty")
        if not self.serial_number or not self.serial_number.strip():
            raise ValueError("serial_number cannot be empty")

    def __str__(self) -> str:
        return f"{self.device_id} ({self.serial_number})"

    def with_center(self, center_id: str) -> "DeviceIdentity":
        """إرجاع نسخة جديدة مع ربط المركز"""
        return DeviceIdentity(
            device_id=self.device_id,
            serial_number=self.serial_number,
            center_id=center_id,
        )
