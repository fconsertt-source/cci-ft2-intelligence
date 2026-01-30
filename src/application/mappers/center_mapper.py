from src.application.dtos.center_dto import CenterDTO


def to_center_dto(center_obj) -> CenterDTO:
    return CenterDTO(
        id=getattr(center_obj, 'id', None),
        name=getattr(center_obj, 'name', ''),
        device_ids=getattr(center_obj, 'device_ids', []),
        ft2_entries=getattr(center_obj, 'ft2_entries', []),
        decision=getattr(center_obj, 'decision', 'UNKNOWN'),
        vvm_stage=getattr(center_obj, 'vvm_stage', 'NONE'),
        alert_level=getattr(center_obj, 'alert_level', None),
        stability_budget_consumed_pct=getattr(center_obj, 'stability_budget_consumed_pct', 0.0),
        thaw_remaining_hours=getattr(center_obj, 'thaw_remaining_hours', None),
        category_display=getattr(center_obj, 'category_display', None),
        decision_reasons=getattr(center_obj, 'decision_reasons', [])
    )
