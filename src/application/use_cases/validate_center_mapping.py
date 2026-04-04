from src.application.ports.i_center_registry import ICenterRegistry
from src.application.services.center_impact_service import CenterImpactService
from src.application.dtos.validation_result import ValidationResult

class ValidateCenterMappingUseCase:
    """
    Use Case: التحقق من تطابق مراكز البيانات مع YAML.
    """

    def __init__(self, center_registry: ICenterRegistry):
        self._registry = center_registry

    def execute(self, centers_from_data: list) -> ValidationResult:
        registered_ids = self._registry.get_all_device_ids()
        yaml_count = self._registry.get_registered_center_count()

        affected_count = CenterImpactService.count_affected_centers(
            centers_from_data
        )
        is_valid, message = CenterImpactService.verify_ssot(
            yaml_count, affected_count
        )

        unregistered = CenterImpactService.get_unregistered_centers(
            centers_from_data,
            registered_ids
        )

        return ValidationResult(
            is_ssot_valid=is_valid,
            yaml_count=yaml_count,
            affected_count=affected_count,
            unregistered_centers=unregistered,
            message=message
        )