from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.domain.value_objects.vaccine_specification import (
    VaccineSpecification, get_vaccine_spec)


def build_spec(name: str = None, **overrides: Any) -> VaccineSpecification:
    """
    Return a VaccineSpecification for tests.

    build_spec(name="OPV")              → real OPV spec from vaccine_library.yaml
    build_spec(name="UNKNOWN_XYZ")      → GENERAL fallback
    build_spec(q10_factor=2.0)          → legacy TEST base spec
    build_spec(name="OPV", q10_factor=2.0) → OPV spec with override
    """
    if name is not None:
        spec = get_vaccine_spec(name.upper())
        if overrides:
            spec = replace(spec, **overrides)
        return spec

    # Legacy fallback (no name given)
    base = dict(
        vaccine_type="TEST",
        q10_factor=2.0,
        shelf_life_days=365,
        freeze_sensitive=False,
        reference_temp_c=5.0,
        critical_temp_c=34.0,
        critical_hours=2.0,
    )
    base.update(overrides)
    return VaccineSpecification(**base)
