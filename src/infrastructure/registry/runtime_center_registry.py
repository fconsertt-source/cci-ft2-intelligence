from typing import Dict, FrozenSet, List, Optional

from src.application.dtos.center_dto import CenterDTO
from src.application.ports.i_center_registry import ICenterRegistry


class RuntimeCenterRegistry(ICenterRegistry):
    """
    Runtime center registry built from loaded center DTOs.

    It is composed at the application boundary and passed to use cases that need
    the center/device single source of truth.
    """

    def __init__(self, centers: List[CenterDTO]):
        self._centers = centers
        self._device_to_center: Dict[str, CenterDTO] = {
            str(unit.device_id): center
            for center in centers
            for unit in center.equipment_units
            if unit.device_id
        }
        self._device_to_center_id: Dict[str, str] = {
            str(unit.device_id): center.id
            for center in centers
            for unit in center.equipment_units
            if unit.device_id
        }

    def get_center_by_device_id(self, device_id: str) -> Optional[CenterDTO]:
        return self._device_to_center.get(str(device_id))

    def get_all_device_ids(self) -> FrozenSet[str]:
        return frozenset(self._device_to_center.keys())

    def get_center_id_for_device(self, device_id: str) -> Optional[str]:
        return self._device_to_center_id.get(str(device_id))

    def get_registered_center_count(self) -> int:
        return len(self._centers)

    def all_centers(self) -> List[CenterDTO]:
        return list(self._centers)
