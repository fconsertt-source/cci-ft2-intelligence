# ft2_linker.py (مُحسّن)
from typing import List, Dict, TYPE_CHECKING
from src.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from src.domain.entities.vaccination_center import VaccinationCenter

logger = get_logger(__name__)

class FT2Linker:
    @staticmethod
    def link(entries: List, centers: List):
        """
        ربط قائمة من الإدخالات بالمراكز (للتوافق مع الكود القديم)
        """
        # استخدام المولد داخلياً لتنفيذ المنطق
        generator = FT2Linker.link_generator(entries, centers)
        # استهلاك المولد لتنفيذ الربط (تحديث كائنات المراكز)
        count = 0
        for _ in generator:
            count += 1
        logger.debug(f"تمت معالجة {count} إدخال عبر خدمة الربط")

    @staticmethod
    def link_generator(entries_generator, centers: List['VaccinationCenter']):
        """ربط الإدخالات كـ Generator لتوفير الذاكرة"""
        device_map = {}
        for center in centers:
            for device_id in center.device_ids:
                device_map[device_id] = center
        
        linked_count = 0
        skipped_count = 0
        
        for entry in entries_generator:
            center = device_map.get(entry.device_id)
            if center:
                center.add_ft2_entry(entry)
                linked_count += 1
                yield entry, center  # إرجاع لكل إدخال
            else:
                skipped_count += 1
                yield entry, None
        
        logger.info(f"تم ربط {linked_count} إدخال، تم تخطي {skipped_count}")