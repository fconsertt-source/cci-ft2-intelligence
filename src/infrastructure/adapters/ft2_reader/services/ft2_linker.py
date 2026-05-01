"""FT2 Linker Service — ربط قراءات FT2 بالمعدات"""
from typing import List, Any
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)  # ← إصلاح: __name__ بدلاً من name

class FT2Linker:
    @staticmethod
    def link(entries: List, centers: List) -> None:
        """ربط قائمة قراءات FT2 بوحدات المعدات"""
        generator = FT2Linker.link_generator(entries, centers)
        count = sum(1 for _ in generator)
        logger.debug("Processed %d entries via linking service", count)

    @staticmethod
    def link_generator(entries_generator, centers: List):
        """ربط قائم على المولدات"""
        device_map = {}

        for center in centers:
            units = getattr(center, "equipment_units", None)
            if units:
                for unit in units:
                    if unit.device_id:
                        device_map[unit.device_id] = unit
            else:
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

        logger.info("Linked %d entries, skipped %d", linked_count, skipped_count)
