from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError, root_validator


class VaccineDefaultsSchema(BaseModel):
    reference_temp_c: float = Field(..., gt=-273.15, description="Reference temperature for HER calibration")
    activation_energy_kj_mol: float = Field(..., gt=0.0, description="Activation energy in kJ/mol")
    degradation_days_at_37C: float = Field(..., gt=0.0, description="Degradation endpoint days at 37°C")
    critical_temp_c: float = Field(..., gt=-273.15)
    critical_hours: float = Field(..., gt=0.0)
    freeze_threshold_c: float = Field(..., description="Freeze threshold")
    ccm_default_limit: int = Field(..., gt=0)
    opened_vial_h: float = Field(..., gt=0.0)
    remaining_shelf_life_min: int = Field(..., ge=0)
    electronic_ccm_device_type: str = Field(...)


class VaccineSpecSchema(BaseModel):
    q10_factor: float = Field(..., gt=0.0)
    shelf_life_days: float = Field(..., gt=0.0)
    freeze_sensitive: bool = Field(...)
    vvm_type: Optional[str] = None
    ccm_limit: Optional[int] = None
    reference_temp_c: float = Field(..., gt=-273.15)
    critical_temp_c: float = Field(..., gt=-273.15)
    critical_hours: float = Field(..., gt=0.0)
    activation_energy_kj_mol: Optional[float] = Field(None, gt=0.0)
    degradation_days_at_37C: Optional[float] = Field(None, gt=0.0)
    storage: Optional[str] = None
    heat_stability: Optional[str] = None
    opened_vial_h: Optional[float] = None
    protect_light: Optional[bool] = None
    shake_test: Optional[bool] = None
    source: Optional[str] = None
    who_code: Optional[str] = None
    active: Optional[bool] = None

    @root_validator
    def check_vvm_and_freeze_sensitivity(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("freeze_sensitive") and values.get("reference_temp_c") < 0:
            raise ValueError("Freeze sensitive vaccines must have reference_temp_c >= 0°C")
        return values


class VaccineLibrarySchema(BaseModel):
    metadata: Dict[str, Any]
    defaults: VaccineDefaultsSchema
    vaccines: Dict[str, VaccineSpecSchema]


def validate_vaccine_library(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        VaccineLibrarySchema(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid vaccine_library.yaml schema: {exc}") from exc
    return data
