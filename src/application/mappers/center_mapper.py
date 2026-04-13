# src/application/mappers/center_mapper.py
from typing import Any, Dict, List

from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.equipment_dto import EquipmentDTO


class CenterMapper:
    """محول وحيد: YAML dict -> CenterDTO (مباشرة، بدون VaccinationCenter)"""

    @staticmethod
    def _build_equipment_units(
        center_id: str,
        equipment_raw: Dict[str, Any],
        temperature_ranges: Dict[str, float],
        decision_thresholds: Dict[str, Any],
    ) -> List[EquipmentDTO]:
        units = []
        for eq_id, eq_data in equipment_raw.items():
            device_id = eq_data.get("device_id", "")
            if not device_id:
                continue
            units.append(EquipmentDTO(
                equipment_id=eq_id,
                equipment_name=eq_data.get("name", eq_id),
                device_id=device_id,
                center_id=center_id,
                temperature_ranges=temperature_ranges,
                decision_thresholds=decision_thresholds,
            ))
        return units

    @staticmethod
    def from_dict_to_dto(center_id: str, data: Dict[str, Any]) -> CenterDTO:
        equipment_raw = data.get("equipment", {})
        temperature_ranges = data.get("temperature_ranges", {"min": 2.0, "max": 8.0})
        decision_thresholds = data.get("decision_thresholds", {})

        equipment_units = CenterMapper._build_equipment_units(
            center_id, equipment_raw, temperature_ranges, decision_thresholds
        )

        return CenterDTO(
            id=center_id,
            name=data.get("name", ""),
            equipment=equipment_raw,
            temperature_ranges=temperature_ranges,
            decision_thresholds=decision_thresholds,
            equipment_units=equipment_units,
        )