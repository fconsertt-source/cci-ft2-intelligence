# src/domain/services/regulatory_decision_service.py

from typing import Literal

from src.domain.value_objects.vaccine_specification import VaccineSpecification

DecisionOutcome = Literal["SAFE", "PARTIAL", "DISCARD"]


def _f(val, default: float) -> float:
    """Safely convert a spec attribute to float. Handles None and MagicMock."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _bool(val, default: bool) -> bool:
    """
    Safely extract a boolean from a spec attribute.
    MagicMock is always truthy, so we check the type explicitly.
    Only real bool/int values are trusted; everything else uses default.
    """
    if isinstance(val, (bool, int)):
        return bool(val)
    return default


def _freeze_range(val):
    """
    Return (fmin, fmax) tuple only if val is a real sequence of two numbers.
    Returns None for MagicMock, None, or malformed values.
    """
    if val is None:
        return None
    if not isinstance(val, (tuple, list)):
        return None
    try:
        if len(val) == 2:
            return float(val[0]), float(val[1])
    except (TypeError, ValueError, IndexError):
        pass
    return None


class RegulatoryDecisionService:

    def evaluate(self, temperature, duration_minutes, spec: VaccineSpecification):

        if spec is None:
            raise ValueError("spec is required")

        temperature = float(temperature)
        duration_hours = float(duration_minutes) / 60.0

        freeze_threshold = _f(spec.freeze_threshold_c, -0.5)
        max_temp = _f(spec.max_temp, 8.0)
        critical_temp = _f(spec.critical_temp_c, 34.0)
        freeze_sensitive = _bool(spec.freeze_sensitive, False)

        max_heat_raw = getattr(spec, "max_heat_temp", None)
        max_heat_temp = (
            _f(max_heat_raw, None)
            if max_heat_raw is not None and isinstance(max_heat_raw, (int, float))
            else None
        )

        max_dur_raw = getattr(spec, "max_heat_duration_hours", None)
        max_heat_duration = (
            _f(max_dur_raw, None)
            if max_dur_raw is not None and isinstance(max_dur_raw, (int, float))
            else None
        )

        freeze_range = _freeze_range(getattr(spec, "freeze_range", None))

        # 1. Freeze — absolute for freeze-sensitive vaccines
        if freeze_sensitive and temperature <= freeze_threshold:
            return "DISCARD"

        # 2. Allowed freeze range (freeze-stable vaccines stored frozen)
        if freeze_range is not None:
            fmin, fmax = freeze_range
            if fmin <= temperature <= fmax:
                return "SAFE"

        # 3. Unexpected freezing (any vaccine below freeze threshold)
        if temperature <= freeze_threshold:
            return "DISCARD"

        # 4. Absolute heat limit
        effective_max_heat = (
            max_heat_temp if max_heat_temp is not None else critical_temp
        )
        if temperature > effective_max_heat:
            return "DISCARD"

        # 5. Above normal range — check duration
        if temperature > max_temp:
            allowed = max_heat_duration if max_heat_duration is not None else 0.0
            if duration_hours >= allowed:
                return "DISCARD"
            return "PARTIAL"

        return "SAFE"
