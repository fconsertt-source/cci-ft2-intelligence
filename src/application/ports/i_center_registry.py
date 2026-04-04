# src/application/ports/i_center_registry.py

from abc import ABC, abstractmethod
from typing import FrozenSet, Dict, Optional

class ICenterRegistry(ABC):

    @abstractmethod
    def get_all_device_ids(self) -> FrozenSet[str]:
        """
        جلب جميع device_ids المسجلة في YAML.
        هذا هو SSOT Check — أي device_id خارج هذه القائمة مرفوض.
        """
        ...

    @abstractmethod
    def get_center_id_for_device(self, device_id: str) -> Optional[str]:
        """جلب center_id لجهاز محدد."""
        ...

    @abstractmethod
    def get_registered_center_count(self) -> int:
        """عدد المراكز المسجلة في YAML. يُستخدم لـ SSOT metric: yaml_count == affected_count"""
        ...