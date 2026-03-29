from typing import Any, Dict, List, Optional
from src.domain.entities.vaccination_center import VaccinationCenter, FreezeTolerance


def make_vaccination_center(
    id: str,
    name: str,
    device_ids: Optional[List[str]] = None,
    equipment: Optional[Dict[str, Dict[str, Any]]] = None,
    temperature_ranges: Optional[Dict[str, float]] = None,
    decision_thresholds: Optional[Dict[str, Any]] = None,
    freeze_tolerance: FreezeTolerance = FreezeTolerance.ZERO_TOLERANCE,
    **kwargs
) -> VaccinationCenter:
    """
    Create a VaccinationCenter instance with compatibility for old-style `device_ids`.
    """
    safe_kwargs = {
        "id": id,
        "name": name,
        "temperature_ranges": temperature_ranges or {"min": 2.0, "max": 8.0},
        "decision_thresholds": decision_thresholds or {},
        "freeze_tolerance": freeze_tolerance,
    }

    if equipment:
        safe_kwargs["equipment"] = equipment
    elif device_ids:
        eq = {}
        for i, did in enumerate(device_ids):
            eq[f"eq_{i}"] = {"device_id": did, "name": f"Device {did}"}
        safe_kwargs["equipment"] = eq

    vc = VaccinationCenter(**safe_kwargs)

    # التوافق مع الاختبارات التي تصل إلى .device_ids
    if device_ids:
        vc.device_ids = device_ids

    return vc
