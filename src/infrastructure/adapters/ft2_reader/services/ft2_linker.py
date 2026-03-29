# src/infrastructure/adapters/ft2_reader/services/ft2_linker.py
from typing import TYPE_CHECKING, Any, List, Protocol

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class LinkableUnit(Protocol):
    """
    واجهة تجريدية للوحدة القابلة للربط ببيانات FT2.
    يمكن أن تكون EquipmentDTO أو أي كائن يحقق هذا Protocol.
    """
    device_ids: List[str]

    def add_ft2_entry(self, entry: Any) -> None: ...


class FT2Linker:
    @staticmethod
    def link(entries: List, centers: List) -> None:
        """
        ربط قائمة من الإدخالات بوحدات المعدات (EquipmentDTO).

        يبني device_map من equipment_units إن وجدت،
        وإلا يرجع للسلوك القديم (التوافق مع الخلف).
        """
        generator = FT2Linker.link_generator(entries, centers)
        count = sum(1 for _ in generator)
        logger.debug("تمت معالجة %d إدخال عبر خدمة الربط", count)

    @staticmethod
    def link_generator(entries_generator, centers: List):
        """
        ربط الإدخالات كـ Generator.

        الاستراتيجية:
        - إذا كان المركز يحتوي على equipment_units → ربط مباشر بالمعدة
        - وإلا → ربط بالمركز مباشرة (توافق مع الخلف)
        """
        device_map = {}

        for center in centers:
            units = getattr(center, "equipment_units", None)
            if units:
                # النظام الجديد: ربط بمستوى المعدة
                for unit in units:
                    if unit.device_id:
                        device_map[unit.device_id] = unit
            else:
                # النظام القديم: ربط بمستوى المركز
                for device_id in getattr(center, "device_ids", []):
                    device_map[device_id] = center

        linked_count = 0
        skipped_count = 0

        for entry in entries_generator:
            target = device_map.get(entry.device_id)
            if target:
                target.add_ft2_entry(entry)
                linked_count += 1
                yield entry, target
            else:
                skipped_count += 1
                yield entry, None

        logger.info("تم ربط %d إدخال، تم تخطي %d", linked_count, skipped_count)