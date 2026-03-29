# src/application/mappers/center_mapper.py
from typing import Any, Dict

from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.equipment_dto import EquipmentDTO
from src.domain.entities.vaccination_center import VaccinationCenter, FreezeTolerance


class CenterMapper:
    """محول وحيد: YAML -> Domain -> DTO"""

    @staticmethod
    def from_dict(center_id: str, data: Dict[str, Any]) -> VaccinationCenter:
        """تحويل القاموس (YAML) إلى Entity — لا تعديل"""
        return VaccinationCenter(
            id=center_id,
            name=data.get("name", ""),
            temperature_ranges=data.get("temperature_ranges", {"min": 2.0, "max": 8.0}),
            decision_thresholds=data.get("decision_thresholds", {}),
            equipment=data.get("equipment", {}),
            freeze_tolerance=data.get("freeze_tolerance", FreezeTolerance.ZERO_TOLERANCE),
        )

    @staticmethod
    def _build_equipment_units(
        center_id: str,
        equipment_raw: Dict[str, Any],
        temperature_ranges: Dict[str, float],
        decision_thresholds: Dict[str, Any],
    ) -> list:
        """بناء قائمة EquipmentDTO من بيانات equipment في YAML"""
        units = []
        for eq_id, eq_data in equipment_raw.items():
            device_id = eq_data.get("device_id", "")
            if not device_id:
                continue  # تجاهل المعدات بدون جهاز FT2
            units.append(
                EquipmentDTO(
                    equipment_id=eq_id,
                    equipment_name=eq_data.get("name", eq_id),
                    device_id=device_id,
                    center_id=center_id,
                    temperature_ranges=temperature_ranges,
                    decision_thresholds=decision_thresholds,
                )
            )
        return units

    @staticmethod
    def to_dto(entity: VaccinationCenter) -> CenterDTO:
        """تحويل Entity إلى CenterDTO مع بناء equipment_units"""
        temperature_ranges = entity.temperature_ranges
        decision_thresholds = entity.decision_thresholds

        equipment_units = CenterMapper._build_equipment_units(
            center_id=entity.id,
            equipment_raw=entity.equipment,
            temperature_ranges=temperature_ranges,
            decision_thresholds=decision_thresholds,
        )

        return CenterDTO(
            id=entity.id,
            name=entity.name,
            equipment=entity.equipment,
            temperature_ranges=temperature_ranges,
            decision_thresholds=decision_thresholds,
            equipment_units=equipment_units,
        )

    @staticmethod
    def from_dict_to_dto(center_id: str, data: Dict[str, Any]) -> CenterDTO:
        """اختصار للتحويل المباشر من البيانات الخام إلى DTO عبر الـ Entity"""
        entity = CenterMapper.from_dict(center_id, data)
        return CenterMapper.to_dto(entity)