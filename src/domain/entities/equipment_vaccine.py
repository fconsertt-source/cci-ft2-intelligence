# src/domain/entities/equipment_vaccine.py
"""
EquipmentVaccine — كيان لقاح داخل معدة تبريد محددة.

يمثل دفعة واحدة من لقاح موجودة في معدة تبريد.
البيانات هجينة:
  - equipment_id, center_id  ← تلقائي من DeviceRegistry/DeviceCenterMapper
  - vaccine_type, batch, expiry, has_vvm, vvm_stage ← يدوي من مدير المخزن
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import IntEnum
from typing import Optional


class VVMStageValue(IntEnum):
    """
    مراحل مؤشر VVM الأربع — WHO/IVB/06.10 Figure 2.

    1 → المربع أفتح من الدائرة          (صالح للاستخدام)
    2 → المربع يقترب من لون الدائرة     (تحذير — استخدم بأولوية)
    3 → المربع = الدائرة                (نقطة الإلغاء — لا تستخدم)
    4 → المربع أغمق من الدائرة          (تجاوز نقطة الإلغاء — تخلص)
    """

    STAGE_1 = 1  # USABLE
    STAGE_2 = 2  # USE_WITH_PRIORITY
    STAGE_3 = 3  # DISCARD
    STAGE_4 = 4  # DISCARD

    @property
    def is_usable(self) -> bool:
        return self.value <= 2

    @property
    def label_ar(self) -> str:
        labels = {
            1: "المرحلة 1 — المربع أفتح من الدائرة (صالح)",
            2: "المرحلة 2 — المربع يقترب من الدائرة (أولوية)",
            3: "المرحلة 3 — المربع = الدائرة (تخلص)",
            4: "المرحلة 4 — المربع أغمق من الدائرة (تخلص)",
        }
        return labels[self.value]


@dataclass(frozen=True)
class EquipmentVaccine:
    """
    دفعة لقاح داخل معدة تبريد — Immutable بعد الإنشاء.

    Attributes:
        entry_id:       معرف فريد للسجل
        equipment_id:   معرف المعدة (تلقائي)
        center_id:      معرف المركز (تلقائي)
        vaccine_type:   نوع اللقاح (يدوي)
        batch_number:   رقم الدفعة (يدوي)
        expiry_date:    تاريخ انتهاء الصلاحية (يدوي)
        quantity_doses: عدد الجرعات (يدوي، اختياري)
        has_vvm:        هل توجد VVM على العبوة؟ (يدوي — checkbox)
        vvm_stage:      مرحلة VVM (يدوي — يظهر فقط إذا has_vvm=True)
        notes:          ملاحظات إضافية (يدوي، اختياري)
        recorded_at:    تاريخ التسجيل (تلقائي)
        recorded_by:    المستخدم المسجِّل (يدوي، اختياري)
    """

    equipment_id: str
    center_id: str
    vaccine_type: str
    batch_number: str
    expiry_date: date

    has_vvm: bool = False
    vvm_stage: Optional[VVMStageValue] = None

    quantity_doses: Optional[int] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.equipment_id or not self.equipment_id.strip():
            raise ValueError("equipment_id cannot be empty")
        if not self.vaccine_type or not self.vaccine_type.strip():
            raise ValueError("vaccine_type cannot be empty")
        if not self.batch_number or not self.batch_number.strip():
            raise ValueError("batch_number cannot be empty")

        # إذا has_vvm=True يجب أن يكون vvm_stage محدداً
        if self.has_vvm and self.vvm_stage is None:
            raise ValueError(
                "vvm_stage مطلوب عند has_vvm=True — " "حدد المرحلة (1/2/3/4)"
            )

        # إذا has_vvm=False يجب أن يكون vvm_stage=None
        if not self.has_vvm and self.vvm_stage is not None:
            raise ValueError("vvm_stage يجب أن يكون None عند has_vvm=False")

    @property
    def is_expired(self) -> bool:
        """هل انتهت صلاحية اللقاح؟"""
        return date.today() > self.expiry_date

    @property
    def vvm_usable(self) -> bool:
        """
        هل مؤشر VVM يشير إلى صلاحية اللقاح؟
        إذا لا يوجد VVM → True (لا يمكن الحكم من VVM)
        """
        if not self.has_vvm or self.vvm_stage is None:
            return True
        return self.vvm_stage.is_usable

    @property
    def days_to_expiry(self) -> int:
        """عدد الأيام المتبقية حتى انتهاء الصلاحية."""
        delta = self.expiry_date - date.today()
        return delta.days

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "equipment_id": self.equipment_id,
            "center_id": self.center_id,
            "vaccine_type": self.vaccine_type,
            "batch_number": self.batch_number,
            "expiry_date": self.expiry_date.isoformat(),
            "quantity_doses": self.quantity_doses,
            "has_vvm": self.has_vvm,
            "vvm_stage": self.vvm_stage.value if self.vvm_stage else None,
            "vvm_stage_label": self.vvm_stage.label_ar if self.vvm_stage else None,
            "notes": self.notes,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentVaccine":
        expiry = data["expiry_date"]
        if isinstance(expiry, str):
            expiry = date.fromisoformat(expiry)

        vvm_stage_raw = data.get("vvm_stage")
        vvm_stage = VVMStageValue(vvm_stage_raw) if vvm_stage_raw else None

        recorded_at = data.get("recorded_at")
        if isinstance(recorded_at, str):
            dt = datetime.fromisoformat(recorded_at)
            recorded_at = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        elif recorded_at is None:
            recorded_at = datetime.now(timezone.utc)

        return cls(
            entry_id=data.get("entry_id", str(uuid.uuid4())),
            equipment_id=data["equipment_id"],
            center_id=data.get("center_id", "UNKNOWN"),
            vaccine_type=data["vaccine_type"],
            batch_number=data["batch_number"],
            expiry_date=expiry,
            quantity_doses=data.get("quantity_doses"),
            has_vvm=data.get("has_vvm", False),
            vvm_stage=vvm_stage,
            notes=data.get("notes"),
            recorded_by=data.get("recorded_by"),
            recorded_at=recorded_at,
        )
