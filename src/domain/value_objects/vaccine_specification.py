# src/domain/value_objects/vaccine_specification.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# System State
# ─────────────────────────────────────────────
class SystemState:
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"


_SYSTEM_STATE = SystemState.NORMAL


# ─────────────────────────────────────────────
# Vaccine Specification
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class VaccineSpecification:

    vaccine_type: str = "GENERAL"
    q10_factor: float = 6.0
    shelf_life_days: int = 730

    freeze_sensitive: bool = False
    vvm_type: Optional[str] = None
    ccm_limit: int = 600

    reference_temp_c: float = 5.0
    critical_temp_c: float = 34.0
    critical_hours: float = 2.0
    freeze_threshold_c: float = -0.5

    min_temp: float = 2.0
    max_temp: float = 8.0

    max_heat_temp: Optional[float] = None
    max_heat_duration_hours: Optional[float] = None
    freeze_range: Optional[Tuple[float, float]] = None

    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    name: Optional[str] = None  # alias used by tests

    # fields accepted by tests
    excursion_time_limit: Optional[float] = None
    storage: Optional[str] = None

    # extra YAML fields — stored as strings, never used in calculations
    heat_stability: Optional[str] = None
    opened_vial_h: Optional[float] = None
    protect_light: Optional[bool] = None
    shake_test: Optional[bool] = None
    note: Optional[str] = None
    who_code: Optional[str] = None
    active: Optional[bool] = None
    who_code: Optional[str] = None
    active: Optional[bool] = None
    ectc_approved: bool = False
    ectc_max_temp_c: Optional[float] = None
    ectc_max_days: Optional[int] = None
    storage_special: Optional[str] = None

    source: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if self.q10_factor is not None and self.q10_factor <= 0:
            raise ValueError(f"{self.vaccine_type}: invalid q10_factor")
        if self.shelf_life_days is not None and self.shelf_life_days <= 0:
            raise ValueError(f"{self.vaccine_type}: invalid shelf life")
        if self.max_temp is not None and self.max_temp <= 0:
            raise ValueError(f"{self.vaccine_type}: invalid max_temp")
        if self.freeze_range is not None and len(self.freeze_range) != 2:
            raise ValueError(f"{self.vaccine_type}: invalid freeze_range")

    @property
    def shelf_life_hours(self) -> Optional[float]:
        if self.shelf_life_days is None:
            return None
        return self.shelf_life_days * 24.0


# ─────────────────────────────────────────────
# YAML Loader
# ─────────────────────────────────────────────

_VACCINE_CATALOGUE: Optional[Dict[str, VaccineSpecification]] = None

REQUIRED_FIELDS = ["q10_factor", "shelf_life_days"]

# Fields in YAML that are NOT constructor params — silently ignored
_YAML_IGNORE = {"ccm_default_limit", "opened_vial_h"}


def _validate_schema(data: Dict):
    if "vaccines" not in data:
        raise RuntimeError("Invalid YAML: missing 'vaccines' section")
    for vid, spec in data["vaccines"].items():
        for f in REQUIRED_FIELDS:
            if f not in spec:
                raise RuntimeError(f"{vid}: missing required field {f}")


def _load_vaccine_library(path: Optional[Path] = None):
    global _VACCINE_CATALOGUE, _SYSTEM_STATE

    if _VACCINE_CATALOGUE:
        return _VACCINE_CATALOGUE

    path = path or Path("config/vaccine_library.yaml")

    if not path.exists():
        _SYSTEM_STATE = SystemState.EMERGENCY
        raise RuntimeError(
            "🚨 يتعذر إصدار التقرير لتلف ملف التطعيمات vaccine_library.yaml"
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        _validate_schema(data)

        defaults = data.get("defaults", {})
        vaccines = data["vaccines"]
        catalogue = {}

        for vid, spec in vaccines.items():
            # Use default arg to capture loop variable correctly
            def get(key, default=None, _spec=spec):
                return _spec.get(key, defaults.get(key, default))

            freeze_range = get("freeze_range")
            if freeze_range is not None:
                freeze_range = tuple(freeze_range)

            name_en = get("name_en")
            catalogue[vid] = VaccineSpecification(
                vaccine_type=vid,
                q10_factor=get("q10_factor"),
                shelf_life_days=get("shelf_life_days"),
                freeze_sensitive=get("freeze_sensitive", False),
                vvm_type=get("vvm_type"),
                reference_temp_c=get("reference_temp_c", 5.0),
                critical_temp_c=get("critical_temp_c", 34.0),
                critical_hours=get("critical_hours", 2.0),
                freeze_threshold_c=get("freeze_threshold_c", -0.5),
                min_temp=get("min_temp", 2.0),
                max_temp=get("max_temp", 8.0),
                max_heat_temp=get("max_heat_temp"),
                max_heat_duration_hours=get("max_heat_duration_hours"),
                freeze_range=freeze_range,
                name_ar=get("name_ar"),
                name_en=name_en,
                name=name_en,
                source=get("source", ""),
                # extra YAML fields — stored safely
                storage=get("storage"),
                heat_stability=get("heat_stability"),
                opened_vial_h=get("opened_vial_h"),
                protect_light=get("protect_light"),
                shake_test=get("shake_test"),
                note=get("note"),
                who_code=get("who_code"),
                active=get("active"),
            )

        _SYSTEM_STATE = SystemState.NORMAL
        _VACCINE_CATALOGUE = catalogue
        return catalogue

    except RuntimeError:
        raise
    except Exception as e:
        _SYSTEM_STATE = SystemState.EMERGENCY
        logger.critical(f"YAML LOAD FAILURE: {e}")
        raise RuntimeError(f"🚨 فشل تحميل vaccine_library.yaml: {str(e)}")


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────


def get_system_state():
    return _SYSTEM_STATE


# في vaccine_specification.py - تعديل بسيط جداً
def get_vaccine_spec(vaccine_type: str) -> VaccineSpecification:
    try:
        catalogue = _load_vaccine_library()
        vaccine_type = vaccine_type.upper()
        if vaccine_type not in catalogue:
            if _SYSTEM_STATE == SystemState.EMERGENCY:
                raise RuntimeError("System in EMERGENCY — cannot resolve vaccine")
            logger.warning(f"Vaccine {vaccine_type} not found, using GENERAL")
            return catalogue.get("GENERAL", VaccineSpecification())
        return catalogue[vaccine_type]
    except Exception as e:
        logger.error(f"Failed to load vaccine spec: {e}, using fallback")
        # Fallback آمن: استخدام GENERAL من الكود الصلب
        return VaccineSpecification()  # GENERAL افتراضي


def get_vaccine_catalogue() -> Dict[str, VaccineSpecification]:
    global _VACCINE_CATALOGUE
    if _VACCINE_CATALOGUE is None:
        _VACCINE_CATALOGUE = _load_vaccine_library()
    return _VACCINE_CATALOGUE
