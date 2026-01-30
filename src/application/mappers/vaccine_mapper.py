from src.application.dtos.vaccine_dto import VaccineDTO


def to_vaccine_dto(vaccine_obj) -> VaccineDTO:
    return VaccineDTO(
        id=getattr(vaccine_obj, 'id', getattr(vaccine_obj, 'vaccine_id', None)),
        category=getattr(vaccine_obj, 'category', None),
        is_freeze_stable=getattr(vaccine_obj, 'is_freeze_stable', False),
        vvm_type=getattr(vaccine_obj, 'vvm_type', None),
        actions=getattr(vaccine_obj, 'actions', None),
        full_loss_threshold_high=getattr(vaccine_obj, 'full_loss_threshold_high', None),
        q10_value=getattr(vaccine_obj, 'q10_value', None),
        ideal_temp=getattr(vaccine_obj, 'ideal_temp', None),
        shelf_life_days=getattr(vaccine_obj, 'shelf_life_days', None),
        thaw_start_time=getattr(vaccine_obj, 'thaw_start_time', None),
        thaw_duration_days=getattr(vaccine_obj, 'thaw_duration_days', 0),
    )
