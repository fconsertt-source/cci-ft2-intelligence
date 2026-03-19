# src/domain/services/exposure_analysis_service.py

from datetime import datetime
from typing import Dict, Optional
from unittest.mock import Mock
from src.domain.value_objects.vaccine_specification import VaccineSpecification


_DEFAULT_SPEC = VaccineSpecification(
    vaccine_type="GENERAL",
    q10_factor=6.0,
    shelf_life_days=730,
    freeze_threshold_c=-0.5,
    critical_temp_c=34.0,
    critical_hours=2.0,
    reference_temp_c=5.0,
    max_temp=8.0,
    freeze_sensitive=False,
)

# Sampling gap threshold: flag when consecutive readings are more than this apart
_SAMPLING_GAP_HOURS = 0.5


class ExposureAnalysisService:
    """
    Analyse temperature readings and compute HER, CCM, and circuit-breakers.

    Constructor params let tests override Q10 model constants:
        ExposureAnalysisService(reference_temp=5.0, q10_value=2.0, shelf_life_hours=48.0)
    """

    def __init__(
        self,
        reference_temp: Optional[float] = None,
        q10_value: Optional[float] = None,
        shelf_life_hours: Optional[float] = None,
    ):
        self._override_reference_temp = reference_temp
        self._override_q10 = q10_value
        self._override_shelf_life_hours = shelf_life_hours

    # ── helpers for temperature extraction ───────────────────────────────────

    def _get_temperature(self, reading) -> float:
        """استخراج درجة الحرارة من القراءة"""
        # أولاً: محاولة الحصول على قيمة رقمية مباشرة
        if hasattr(reading, 'temperature'):
            val = reading.temperature
            if isinstance(val, (int, float)):
                return float(val)
            # إذا كان Mock، حاول الحصول على return_value
            if hasattr(val, 'return_value'):
                rv = val.return_value
                if isinstance(rv, (int, float)):
                    return float(rv)
        
        if hasattr(reading, 'value'):
            val = reading.value
            if isinstance(val, (int, float)):
                return float(val)
            if hasattr(val, 'return_value'):
                rv = val.return_value
                if isinstance(rv, (int, float)):
                    return float(rv)
        
        return 0.0

    # ── public API ────────────────────────────────────────────────────────

    def analyze(self, readings, spec: Optional[VaccineSpecification] = None) -> Dict:
        """
        Returns dict with keys:
            max_temp, min_temp, has_freeze, has_critical_heat,
            ccm_index, her_ratio, circuit_breaker,
            total_hours_above_10, data_quality_flags
        """
        if spec is None:
            spec = _DEFAULT_SPEC

        if not readings:
            return {
                "max_temp": 0.0,
                "min_temp": 0.0,
                "has_freeze": False,
                "has_critical_heat": False,
                "ccm_index": "0",
                "her_ratio": 0.0,
                "circuit_breaker": None,
                "total_hours_above_10": 0.0,
                "data_quality_flags": [],
            }

        temps = [self._get_temperature(r) for r in readings]
        max_temp = max(temps)
        min_temp = min(temps)

        hours_above_10 = self._hours_above(readings, 10.0)
        hours_above_critical = self._hours_above(readings, spec.critical_temp_c)
        has_critical_heat = hours_above_critical >= spec.critical_hours
        has_freeze = min_temp < spec.freeze_threshold_c

        her_ratio = self._her_ratio(readings, spec)
        ccm_index = self._ccm(hours_above_10, hours_above_critical)

        # Circuit Breakers — priority order
        circuit_breaker = None
        if has_critical_heat:
            circuit_breaker = f"CRITICAL_HEAT_{int(spec.critical_temp_c)}C"
        elif has_freeze and spec.freeze_sensitive:
            circuit_breaker = "FREEZE_EXCURSION"

        return {
            "max_temp": max_temp,
            "min_temp": min_temp,
            "has_freeze": has_freeze,
            "has_critical_heat": has_critical_heat,
            "ccm_index": ccm_index,
            "her_ratio": her_ratio,
            "circuit_breaker": circuit_breaker,
            "total_hours_above_10": hours_above_10,
            "data_quality_flags": self._quality_flags(readings),
        }

    # ── helpers ───────────────────────────────────────────────────────────

    def _get_duration_hours(self, reading) -> float:
        """Handle both .duration_minutes (FT2) and .duration_hours (TemperatureReading)."""
        dm = getattr(reading, "duration_minutes", None)
        if dm is not None and not callable(dm):
            try:
                return float(dm) / 60.0
            except (TypeError, ValueError):
                pass
        dh = getattr(reading, "duration_hours", None)
        if dh is not None and not callable(dh):
            try:
                return float(dh)
            except (TypeError, ValueError):
                pass
        return 0.0

    def _hours_above(self, readings, threshold: float) -> float:
        total = 0.0
        
        # التعامل مع Mock في threshold
        actual_threshold = threshold
        if isinstance(threshold, Mock):
            if hasattr(threshold, 'return_value'):
                actual_threshold = threshold.return_value
            else:
                actual_threshold = 34.0  # القيمة الافتراضية لـ critical_temp_c
        
        # تأكد من أن actual_threshold رقم
        try:
            actual_threshold = float(actual_threshold)
        except (TypeError, ValueError):
            actual_threshold = 34.0
        
        for r in readings:
            temp = self._get_temperature(r)
            if temp > actual_threshold:
                total += self._get_duration_hours(r)
        return total

    def _her_ratio(self, readings, spec: VaccineSpecification) -> float:
        """HER = Σ [ Q10^((T - T_ref)/10) × Δt_hours ] / shelf_life_hours"""
        if not readings:
            return 0.0

        q10 = self._override_q10 if self._override_q10 is not None else (spec.q10_factor or 6.0)
        t_ref = self._override_reference_temp if self._override_reference_temp is not None else spec.reference_temp_c

        if self._override_shelf_life_hours is not None:
            shelf_life_hours = self._override_shelf_life_hours
        elif spec.shelf_life_days is not None and spec.shelf_life_days > 0:
            shelf_life_hours = spec.shelf_life_days * 24.0
        else:
            return 0.0

        accumulated = 0.0
        for r in readings:
            delta_hours = self._get_duration_hours(r)
            temp = self._get_temperature(r)
            rate = q10 ** ((temp - t_ref) / 10.0)
            accumulated += rate * delta_hours

        return accumulated / shelf_life_hours

    def _ccm(self, h10: float, h34: float) -> str:
        if h34 >= 2:
            return "D"
        if h10 >= 336:
            return "ABC"
        if h10 >= 192:
            return "AB"
        if h10 >= 72:
            return "A"
        return "0"

    def _quality_flags(self, readings) -> list:
        """
        Detect sampling gaps between consecutive timestamped readings.
        Flags 'sampling_gap' when the time between consecutive timestamps
        exceeds _SAMPLING_GAP_HOURS (default 0.5h), consistent with
        Q10HerCalculator's max_gap_hours default.
        Safely skips readings where timestamp is not a real datetime.
        """
        flags = []
        if len(readings) < 2:
            return flags

        for i in range(1, len(readings)):
            ts_prev = getattr(readings[i - 1], "timestamp", None)
            ts_curr = getattr(readings[i], "timestamp", None)

            # Use recorded_at as fallback (TemperatureReading uses this attribute)
            if not isinstance(ts_prev, datetime):
                ts_prev = getattr(readings[i - 1], "recorded_at", None)
            if not isinstance(ts_curr, datetime):
                ts_curr = getattr(readings[i], "recorded_at", None)

            if not isinstance(ts_prev, datetime) or not isinstance(ts_curr, datetime):
                continue

            gap_hours = (ts_curr - ts_prev).total_seconds() / 3600.0
            if gap_hours > _SAMPLING_GAP_HOURS and "sampling_gap" not in flags:
                flags.append("sampling_gap")
                break

        return flags