from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Tuple

from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest,
)
from src.domain.services.scientific_reference_service import ScientificReferenceService
from src.domain.value_objects.temperature_entry import TemperatureEntry


class EvaluateScientificReferenceUseCase:
    """
    Use case that executes the parallel reference audit path without changing the legacy decision.
    """

    def __init__(self, reference_service: ScientificReferenceService) -> None:
        self._reference_service = reference_service

    def _build_entries(self, readings: Tuple[TemperatureEntry, ...]) -> list[TemperatureEntry]:
        entries = []
        if not readings:
            return entries

        sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        for current, nxt in zip(sorted_readings, sorted_readings[1:]):
            duration_minutes = max(0.0, (nxt.timestamp - current.timestamp).total_seconds() / 60.0)
            entries.append(
                TemperatureEntry(
                    temperature=current.value,
                    timestamp=current.timestamp,
                    duration_minutes=duration_minutes,
                    device_id=current.device_id,
                )
            )

        last = sorted_readings[-1]
        entries.append(
            TemperatureEntry(
                temperature=last.value,
                timestamp=last.timestamp,
                duration_minutes=0.0,
                device_id=last.device_id,
            )
        )
        return entries

    def execute(self, request: EvaluateColdChainSafetyRequest) -> Dict[str, Optional[object]]:
        vaccine_type = None
        if request.vaccine_spec is not None:
            vaccine_type = request.vaccine_spec.vaccine_type
        elif request.vaccine_inventory is not None:
            vaccine_type = request.vaccine_inventory.get("vaccine_type")

        entries = self._build_entries(request.readings)
        return self._reference_service.analyze(
            entries=entries,
            vaccine_type=vaccine_type,
        )
