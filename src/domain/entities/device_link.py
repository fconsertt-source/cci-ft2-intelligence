# src/domain/entities/device_link.py
"""
DeviceLink — سجل استبدال جهاز بآخر مع الحفاظ على اتصال سلسلة التبريد.

المبدأ الأساسي:
  عند استبدال جهاز قديم بجديد يجب أن:
  1. تُسجَّل لحظة التسليم بدقة (handover_date)
  2. تُحسب الفجوة الزمنية بين توقف القديم وبدء الجديد
  3. يُحكم على اتصال السلسلة (cold_chain_intact)
  4. يظل السجل التاريخي للجهاز القديم متاحاً عبر الربط

قاعدة الفجوة المقبولة:
  ≤ 2 ساعة  → السلسلة متصلة   (cold_chain_intact = True)
  > 2 ساعة  → فجوة محتملة     (cold_chain_intact = False)
  المصدر: WHO/PQS/E06/IN02.1 § 4.2.3 (عتبة النافذة D = ساعتان فوق 34°C)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# الفجوة الزمنية المقبولة بالساعات قبل اعتبار السلسلة منقطعة
_MAX_ACCEPTABLE_GAP_HOURS: float = 2.0


@dataclass(frozen=True)
class DeviceLink:
    """
    سجل ربط جهاز قديم بجهاز جديد — Immutable بعد الإنشاء.

    Attributes:
        link_id:            معرف فريد للسجل
        old_device_id:      معرف الجهاز القديم (RETIRED/REPLACED)
        new_device_id:      معرف الجهاز الجديد (ACTIVE)
        equipment_id:       معرف معدة التبريد المشتركة بين الجهازين
        handover_date:      تاريخ ووقت التسليم الفعلي
        old_device_last_reading: آخر قراءة سجلها الجهاز القديم
        new_device_first_reading: أول قراءة سجلها الجهاز الجديد
        gap_hours:          الفجوة الزمنية المحسوبة بالساعات
        cold_chain_intact:  هل السلسلة متصلة؟ (gap ≤ 2 ساعة)
        gap_reason:         سبب الفجوة إن وجدت (صيانة / عطل / ...)
        created_at:         تاريخ إنشاء هذا السجل
        created_by:         المستخدم الذي أنشأ السجل
    """

    old_device_id: str
    new_device_id: str
    equipment_id: str
    handover_date: datetime

    # القراءات الحدية — تُستخدم لحساب الفجوة الفعلية
    old_device_last_reading: Optional[datetime] = None
    new_device_first_reading: Optional[datetime] = None

    # محسوبة تلقائياً في __post_init__
    gap_hours: float = field(default=0.0)
    cold_chain_intact: bool = field(default=True)

    # معلومات إضافية
    gap_reason: Optional[str] = None
    created_by: Optional[str] = None

    # معرف وتاريخ الإنشاء — يُولَّدان تلقائياً
    link_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """حساب gap_hours و cold_chain_intact تلقائياً عند الإنشاء."""
        if not self.old_device_id or not self.old_device_id.strip():
            raise ValueError("old_device_id cannot be empty")
        if not self.new_device_id or not self.new_device_id.strip():
            raise ValueError("new_device_id cannot be empty")
        if self.old_device_id == self.new_device_id:
            raise ValueError("old_device_id and new_device_id must be different")
        if not self.equipment_id or not self.equipment_id.strip():
            raise ValueError("equipment_id cannot be empty")

        # حساب الفجوة من القراءات الحدية إن توفرت
        computed_gap = self._compute_gap()
        object.__setattr__(self, "gap_hours", computed_gap)
        object.__setattr__(
            self,
            "cold_chain_intact",
            computed_gap <= _MAX_ACCEPTABLE_GAP_HOURS,
        )

    def _compute_gap(self) -> float:
        """
        حساب الفجوة الزمنية بالساعات.

        المنطق:
          - إذا توفرت كلتا القراءتان → الفجوة = الفرق بينهما
          - إذا توفرت واحدة فقط → الفجوة = 0 (نفترض الاتصال)
          - إذا لم تتوفر أي منهما → الفجوة = 0
        """
        if self.old_device_last_reading and self.new_device_first_reading:
            # توحيد التوقيت إلى UTC
            old_last = self._to_utc(self.old_device_last_reading)
            new_first = self._to_utc(self.new_device_first_reading)

            delta = new_first - old_last
            gap = delta.total_seconds() / 3600.0

            # الفجوة لا تكون سالبة (خطأ في البيانات)
            return max(0.0, round(gap, 4))

        return 0.0

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        """توحيد التوقيت إلى UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    def create(
        cls,
        old_device_id: str,
        new_device_id: str,
        equipment_id: str,
        handover_date: datetime,
        old_device_last_reading: Optional[datetime] = None,
        new_device_first_reading: Optional[datetime] = None,
        gap_reason: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> "DeviceLink":
        """
        مصنع لإنشاء سجل ربط جديد.

        Args:
            old_device_id:           معرف الجهاز القديم
            new_device_id:           معرف الجهاز الجديد
            equipment_id:            معرف معدة التبريد
            handover_date:           تاريخ التسليم الفعلي
            old_device_last_reading: آخر قراءة للجهاز القديم
            new_device_first_reading: أول قراءة للجهاز الجديد
            gap_reason:              سبب الفجوة إن وجدت
            created_by:              المستخدم المنشئ

        Returns:
            DeviceLink جاهز مع gap_hours و cold_chain_intact محسوبَين
        """
        return cls(
            old_device_id=old_device_id,
            new_device_id=new_device_id,
            equipment_id=equipment_id,
            handover_date=handover_date,
            old_device_last_reading=old_device_last_reading,
            new_device_first_reading=new_device_first_reading,
            gap_reason=gap_reason,
            created_by=created_by,
        )

    def to_dict(self) -> dict:
        """تحويل السجل إلى قاموس للتخزين."""
        return {
            "link_id": self.link_id,
            "old_device_id": self.old_device_id,
            "new_device_id": self.new_device_id,
            "equipment_id": self.equipment_id,
            "handover_date": self.handover_date.isoformat(),
            "old_device_last_reading": (
                self.old_device_last_reading.isoformat()
                if self.old_device_last_reading
                else None
            ),
            "new_device_first_reading": (
                self.new_device_first_reading.isoformat()
                if self.new_device_first_reading
                else None
            ),
            "gap_hours": self.gap_hours,
            "cold_chain_intact": self.cold_chain_intact,
            "gap_reason": self.gap_reason,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeviceLink":
        """إعادة بناء السجل من قاموس."""

        def _parse_dt(val: Optional[str]) -> Optional[datetime]:
            if not val:
                return None
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        return cls(
            link_id=data.get("link_id", str(uuid.uuid4())),
            old_device_id=data["old_device_id"],
            new_device_id=data["new_device_id"],
            equipment_id=data["equipment_id"],
            handover_date=_parse_dt(data["handover_date"]),
            old_device_last_reading=_parse_dt(
                data.get("old_device_last_reading")
            ),
            new_device_first_reading=_parse_dt(
                data.get("new_device_first_reading")
            ),
            gap_reason=data.get("gap_reason"),
            created_by=data.get("created_by"),
            created_at=_parse_dt(data.get("created_at"))
            or datetime.now(timezone.utc),
        )

    def __str__(self) -> str:
        status = "✅ متصلة" if self.cold_chain_intact else "❌ فجوة"
        return (
            f"DeviceLink [{self.old_device_id} → {self.new_device_id}] "
            f"معدة={self.equipment_id} "
            f"فجوة={self.gap_hours:.2f}h {status}"
        )