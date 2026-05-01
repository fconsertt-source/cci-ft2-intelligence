from types import SimpleNamespace

from src.application.dtos.center_dto import CenterDTO
from src.infrastructure.registry.runtime_center_registry import RuntimeCenterRegistry


def test_get_center_by_device_id():
    center = CenterDTO(
        id="C001",
        name="Center 1",
        equipment_units=[SimpleNamespace(device_id="DEV001")],
    )

    registry = RuntimeCenterRegistry([center])

    assert registry.get_center_by_device_id("DEV001") == center
    assert registry.get_center_id_for_device("DEV001") == "C001"
    assert registry.get_all_device_ids() == frozenset({"DEV001"})
    assert registry.get_registered_center_count() == 1
