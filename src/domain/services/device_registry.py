# src/domain/services/device_registry.py
"""
DeviceRegistry — سجل الأجهزة المركزي.

مسؤوليات:
  - تسجيل الأجهزة الجديدة
  - تقاعد الأجهزة القديمة
  - استبدال جهاز بآخر مع حفظ سجل الربط
  - إعادة بناء السلسلة الزمنية الكاملة لأي معدة
  - الحكم على اتصال سلسلة التبريد عبر الزمن
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.domain.entities.device_link import DeviceLink
from src.domain.enums.device_status import DeviceStatus

logger = logging.getLogger(__name__)


class DeviceRecord:
    """
    سجل جهاز واحد في الـ Registry.
    mutable — يتغير عند تغيير الحالة.
    """

    def __init__(
        self,
        device_id: str,
        serial_number: str,
        equipment_id: str,
        status: DeviceStatus = DeviceStatus.ACTIVE,
        registered_at: Optional[datetime] = None,
        retired_at: Optional[datetime] = None,
        replaced_by: Optional[str] = None,
    ) -> None:
        self.device_id = device_id
        self.serial_number = serial_number
        self.equipment_id = equipment_id
        self.status = status
        self.registered_at = registered_at or datetime.now(timezone.utc)
        self.retired_at = retired_at
        self.replaced_by = replaced_by

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "serial_number": self.serial_number,
            "equipment_id": self.equipment_id,
            "status": self.status.value,
            "registered_at": self.registered_at.isoformat(),
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
            "replaced_by": self.replaced_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeviceRecord":
        def _parse_dt(val):
            if not val:
                return None
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        return cls(
            device_id=data["device_id"],
            serial_number=data.get("serial_number", "UNKNOWN"),
            equipment_id=data["equipment_id"],
            status=DeviceStatus(data.get("status", "ACTIVE")),
            registered_at=_parse_dt(data.get("registered_at")),
            retired_at=_parse_dt(data.get("retired_at")),
            replaced_by=data.get("replaced_by"),
        )


class DeviceRegistry:
    """
    سجل الأجهزة المركزي — يدير دورة حياة كل جهاز.

    التخزين: ملفان JSON في data/registry/
      - devices.json    → سجل الأجهزة
      - links.json      → سجل الاستبدالات
    """

    def __init__(self, registry_dir: Path) -> None:
        self._dir = Path(registry_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._devices_path = self._dir / "devices.json"
        self._links_path = self._dir / "links.json"

        # تحميل البيانات من الملفات
        self._devices: Dict[str, DeviceRecord] = self._load_devices()
        self._links: List[DeviceLink] = self._load_links()

    # ──────────────────────────────────────────────────────────
    # عمليات الأجهزة
    # ──────────────────────────────────────────────────────────

    def register_device(
        self,
        device_id: str,
        serial_number: str,
        equipment_id: str,
    ) -> DeviceRecord:
        """
        تسجيل جهاز جديد.

        Raises:
            ValueError: إذا كان الجهاز مسجلاً مسبقاً
        """
        if device_id in self._devices:
            raise ValueError(
                f"الجهاز {device_id} مسجل مسبقاً "
                f"بحالة {self._devices[device_id].status.value}"
            )

        record = DeviceRecord(
            device_id=device_id,
            serial_number=serial_number,
            equipment_id=equipment_id,
            status=DeviceStatus.ACTIVE,
        )
        self._devices[device_id] = record
        self._save_devices()

        logger.info(
            "تم تسجيل جهاز جديد: %s (معدة: %s)", device_id, equipment_id
        )
        return record

    def replace_device(
        self,
        old_device_id: str,
        new_device_id: str,
        new_serial_number: str,
        handover_date: datetime,
        old_device_last_reading: Optional[datetime] = None,
        new_device_first_reading: Optional[datetime] = None,
        gap_reason: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> DeviceLink:
        """
        استبدال جهاز قديم بجديد مع إنشاء سجل الربط.

        الخطوات:
          1. التحقق من وجود الجهاز القديم وأنه ACTIVE
          2. تحديث حالة القديم إلى REPLACED
          3. تسجيل الجهاز الجديد كـ ACTIVE
          4. إنشاء DeviceLink يربط القديم بالجديد
          5. حفظ كل شيء

        Args:
            old_device_id:           معرف الجهاز القديم
            new_device_id:           معرف الجهاز الجديد
            new_serial_number:       الرقم التسلسلي للجهاز الجديد
            handover_date:           تاريخ التسليم الفعلي
            old_device_last_reading: آخر قراءة للجهاز القديم
            new_device_first_reading: أول قراءة للجهاز الجديد
            gap_reason:              سبب الفجوة إن وجدت
            created_by:              المستخدم المنفذ

        Returns:
            DeviceLink يحتوي gap_hours و cold_chain_intact

        Raises:
            ValueError: إذا كان الجهاز القديم غير موجود أو غير ACTIVE
        """
        # التحقق من الجهاز القديم
        if old_device_id not in self._devices:
            raise ValueError(f"الجهاز القديم {old_device_id} غير موجود في السجل")

        old_record = self._devices[old_device_id]
        if old_record.status != DeviceStatus.ACTIVE:
            raise ValueError(
                f"الجهاز {old_device_id} غير نشط "
                f"(حالته: {old_record.status.value})"
            )

        # التحقق من عدم تسجيل الجهاز الجديد مسبقاً
        if new_device_id in self._devices:
            raise ValueError(
                f"الجهاز الجديد {new_device_id} مسجل مسبقاً"
            )

        equipment_id = old_record.equipment_id

        # 1. تحديث الجهاز القديم → REPLACED
        old_record.status = DeviceStatus.REPLACED
        old_record.retired_at = handover_date
        old_record.replaced_by = new_device_id

        # 2. تسجيل الجهاز الجديد
        new_record = DeviceRecord(
            device_id=new_device_id,
            serial_number=new_serial_number,
            equipment_id=equipment_id,
            status=DeviceStatus.ACTIVE,
            registered_at=handover_date,
        )
        self._devices[new_device_id] = new_record

        # 3. إنشاء DeviceLink
        link = DeviceLink.create(
            old_device_id=old_device_id,
            new_device_id=new_device_id,
            equipment_id=equipment_id,
            handover_date=handover_date,
            old_device_last_reading=old_device_last_reading,
            new_device_first_reading=new_device_first_reading,
            gap_reason=gap_reason,
            created_by=created_by,
        )
        self._links.append(link)

        # 4. حفظ
        self._save_devices()
        self._save_links()

        logger.info(
            "استبدال الجهاز: %s → %s | فجوة=%.2fh | سلسلة=%s",
            old_device_id,
            new_device_id,
            link.gap_hours,
            "متصلة ✅" if link.cold_chain_intact else "منقطعة ❌",
        )

        return link

    def retire_device(
        self,
        device_id: str,
        reason: Optional[str] = None,
    ) -> DeviceRecord:
        """
        تقاعد جهاز دون استبداله (انتهاء الصلاحية / العطل النهائي).

        Raises:
            ValueError: إذا كان الجهاز غير موجود أو غير ACTIVE
        """
        if device_id not in self._devices:
            raise ValueError(f"الجهاز {device_id} غير موجود في السجل")

        record = self._devices[device_id]
        if record.status != DeviceStatus.ACTIVE:
            raise ValueError(
                f"الجهاز {device_id} ليس نشطاً "
                f"(حالته: {record.status.value})"
            )

        record.status = DeviceStatus.RETIRED
        record.retired_at = datetime.now(timezone.utc)

        self._save_devices()

        logger.info("تم تقاعد الجهاز: %s | السبب: %s", device_id, reason)
        return record

    # ──────────────────────────────────────────────────────────
    # استعلامات
    # ──────────────────────────────────────────────────────────

    def get_device(self, device_id: str) -> Optional[DeviceRecord]:
        """جلب سجل جهاز بمعرفه."""
        return self._devices.get(device_id)

    def get_active_device_for_equipment(
        self, equipment_id: str
    ) -> Optional[DeviceRecord]:
        """جلب الجهاز النشط حالياً لمعدة معينة."""
        for record in self._devices.values():
            if (
                record.equipment_id == equipment_id
                and record.status == DeviceStatus.ACTIVE
            ):
                return record
        return None

    def get_device_chain(self, equipment_id: str) -> List[DeviceRecord]:
        """
        إعادة بناء السلسلة الزمنية الكاملة للأجهزة على معدة معينة.

        المخرج: قائمة مرتبة من الأقدم للأحدث عبر سلسلة الاستبدال الفعلية.

        المنطق:
          - نبدأ من الجهاز الذي لا يظهر كـ new_device في أي link
            (أي الجهاز الأصلي الأول)
          - نتبع replaced_by حتى نصل للجهاز الأحدث
          - إذا لم توجد links نرجع الأجهزة مرتبة بـ registered_at
        """
        # جمع الأجهزة المرتبطة بهذه المعدة
        eq_devices = {
            r.device_id: r
            for r in self._devices.values()
            if r.equipment_id == equipment_id
        }

        if not eq_devices:
            return []

        # إذا لا توجد links → ترتيب بسيط بـ registered_at
        eq_links = [
            lnk for lnk in self._links
            if lnk.equipment_id == equipment_id
        ]

        if not eq_links:
            return sorted(eq_devices.values(), key=lambda r: r.registered_at)

        # تحديد الجهاز الأول: لا يظهر كـ new_device في أي link
        new_device_ids = {lnk.new_device_id for lnk in eq_links}
        first_devices = [
            dev_id for dev_id in eq_devices
            if dev_id not in new_device_ids
        ]

        if not first_devices:
            # fallback — رتّب بـ registered_at
            return sorted(eq_devices.values(), key=lambda r: r.registered_at)

        # بناء السلسلة بتتبع replaced_by
        chain = []
        current_id = first_devices[0]

        while current_id and current_id in eq_devices:
            record = eq_devices[current_id]
            chain.append(record)
            current_id = record.replaced_by

        # إضافة أي أجهزة لم تُضَم (حالة غير متوقعة)
        for dev_id, record in eq_devices.items():
            if record not in chain:
                chain.append(record)

        return chain

    def get_links_for_equipment(self, equipment_id: str) -> List[DeviceLink]:
        """جلب جميع سجلات الاستبدال لمعدة معينة مرتبة زمنياً."""
        links = [
            lnk for lnk in self._links
            if lnk.equipment_id == equipment_id
        ]
        return sorted(links, key=lambda lnk: lnk.handover_date)

    def is_cold_chain_intact(self, equipment_id: str) -> bool:
        """
        الحكم على اتصال سلسلة التبريد الكاملة لمعدة معينة.

        تعود False إذا كان أي سجل استبدال يحتوي على فجوة > 2 ساعة.
        """
        links = self.get_links_for_equipment(equipment_id)
        return all(lnk.cold_chain_intact for lnk in links)

    def get_all_device_ids_for_equipment(
        self, equipment_id: str
    ) -> List[str]:
        """
        جلب جميع معرفات الأجهزة (قديمة وجديدة) لمعدة معينة.
        يُستخدم لجلب السجل التاريخي الكامل من ft2_data.json.
        """
        return [
            r.device_id
            for r in self.get_device_chain(equipment_id)
        ]

    # ──────────────────────────────────────────────────────────
    # التخزين
    # ──────────────────────────────────────────────────────────

    def _load_devices(self) -> Dict[str, DeviceRecord]:
        if not self._devices_path.exists():
            return {}
        try:
            with open(self._devices_path, encoding="utf-8") as f:
                data = json.load(f)
            return {
                item["device_id"]: DeviceRecord.from_dict(item)
                for item in data
            }
        except Exception as e:
            logger.error("فشل تحميل devices.json: %s", e)
            return {}

    def _load_links(self) -> List[DeviceLink]:
        if not self._links_path.exists():
            return []
        try:
            with open(self._links_path, encoding="utf-8") as f:
                data = json.load(f)
            return [DeviceLink.from_dict(item) for item in data]
        except Exception as e:
            logger.error("فشل تحميل links.json: %s", e)
            return []

    def _save_devices(self) -> None:
        with open(self._devices_path, "w", encoding="utf-8") as f:
            json.dump(
                [r.to_dict() for r in self._devices.values()],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def _save_links(self) -> None:
        with open(self._links_path, "w", encoding="utf-8") as f:
            json.dump(
                [lnk.to_dict() for lnk in self._links],
                f,
                ensure_ascii=False,
                indent=2,
            )