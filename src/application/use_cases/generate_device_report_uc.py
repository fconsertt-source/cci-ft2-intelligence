#!/usr/bin/env python3
"""Generate Device Report Use Case — حالة استخدام توليد تقرير الجهاز"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

from src.application.ports.device_repository_port import DeviceRepositoryPort
from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.application.ports.vaccine_specification_port import VaccineSpecificationPort
from src.application.ports.validation_protocol_port import ValidationProtocolPort
from src.application.security.license_guard import LicenseGuard

# request DTO moved to dedicated module to satisfy Phase 3 contract
from src.application.use_cases.requests import GenerateDeviceReportRequest
from src.domain.dtos.device_report_dto import DeviceReportDTO, ThermalExcursionDTO
from src.domain.entities.thermal_record import ThermalRecord
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.enums.regulatory_status import RegulatoryStatus
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import (
    ThermalDegradationEstimator,
)


class GenerateDeviceReportUseCase:
    def __init__(
        self,
        device_repository: DeviceRepositoryPort,
        vaccine_specifications: VaccineSpecificationPort,
        regulatory_decision_service: RegulatoryDecisionService,
        estimator: ThermalDegradationEstimator,
        validator: ValidationProtocolPort,
        license_guard: LicenseGuard,
        ledger_writer: Optional[LedgerWriterPort] = None,
        data_path: Optional[Path] = None,
    ):
        self._repo = device_repository
        self._specs = vaccine_specifications
        self._regulatory_decision = regulatory_decision_service
        self._estimator = estimator
        self._validator = validator
        self._guard = license_guard
        self._ledger_writer = ledger_writer
        self._data_path = data_path or Path("data")

    def execute(
        self, request: Optional[GenerateDeviceReportRequest] = None, **kwargs
    ) -> DeviceReportDTO:
        # 🔹 Backward compatibility bridge
        # Handles execute(device_id="...") and execute("...")
        if not isinstance(request, GenerateDeviceReportRequest):
            device_id = kwargs.get("device_id") or request
            if not device_id:
                raise TypeError(
                    "execute() requires a request object or a device_id argument"
                )
            request = GenerateDeviceReportRequest(device_id=device_id)

        self._guard.ensure_active()

        if self._ledger_writer:
            # convert enums to strings for compatibility with the writer
            self._ledger_writer.append(
                event_type=str(LedgerEvent.OPERATOR_SESSION_STARTED),
                operator=request.operator,
                file_hash="N/A",  # Not file-specific
                ft2_serial=request.device_id,
                cycle_id=request.cycle_id,
            )

        records = self._retrieve_device_timeline(
            request.device_id, request.date_from, request.date_to
        )
        spec = self._fetch_vaccine_specification(records)
        excursions, final_status = self._evaluate_timeline_regulatory(records, spec)

        advisory_info = self._estimator.calculate_cumulative_impact(
            thermal_history=records, spec=spec
        )

        validation_required = None
        if final_status == RegulatoryStatus.PARTIAL.name and self._validator:
            validation_required = self._validator.get_protocol(spec.vaccine_type)

        report = DeviceReportDTO(
            device_id=request.device_id,
            vaccine_type=spec.vaccine_type,
            total_records=len(records),
            excursions=excursions,
            final_status=final_status,
            scientific_rationale=spec.rationale,
            advisory_section=advisory_info,
            validation_required=validation_required,
            operator=request.operator,
            cycle_id=request.cycle_id,
        )

        if self._ledger_writer:
            report_hash = hashlib.sha256(
                json.dumps(
                    {
                        "device_id": request.device_id,
                        "final_status": final_status,
                        "generated_at": report.generated_at,
                    },
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            self._ledger_writer.append(
                event_type=str(LedgerEvent.REPORT_GENERATED),
                ft2_serial=request.device_id,
                file_hash=report_hash,
                operator=request.operator,
                cycle_id=request.cycle_id,
                batch_counts=report.get_batch_counts(),
            )
            self._ledger_writer.append(
                event_type=str(LedgerEvent.OPERATOR_SESSION_ENDED),
                operator=request.operator,
                file_hash="N/A",
                ft2_serial=request.device_id,
                cycle_id=request.cycle_id,
            )

        return report

    def _retrieve_device_timeline(
        self,
        device_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[ThermalRecord]:
        try:
            # ✅ Call repo with kwargs only if they are not None
            if date_from is None and date_to is None:
                records = self._repo.get_device_history(device_id)
            else:
                records = self._repo.get_device_history(
                    device_id, date_from=date_from, date_to=date_to
                )
        except TypeError:
            # حل بديل للتوافق مع الإصدارات القديمة من المستودعات التي لا تدعم الفلترة
            records = self._repo.get_device_history(device_id)  # type: ignore

        if not records:
            error_msg = f"No thermal history found for device: {device_id}"
            if date_from or date_to:
                error_msg += " within the specified date range."
            raise ValueError(error_msg)
        return records

    def _fetch_vaccine_specification(self, records: List[ThermalRecord]) -> Any:
        return self._specs.get_spec(records[0].vaccine_type)

    def _evaluate_timeline_regulatory(
        self, records: List[ThermalRecord], spec: Any
    ) -> Tuple[List[ThermalExcursionDTO], str]:
        excursions: List[ThermalExcursionDTO] = []
        weakest_status = RegulatoryStatus.SAFE

        for record in records:
            impact_str = self._regulatory_decision.evaluate(
                temperature=record.temperature,
                duration_minutes=record.duration_minutes,
                spec=spec,
            )
            impact_enum = getattr(RegulatoryStatus, impact_str, RegulatoryStatus.SAFE)
            if impact_enum.value > weakest_status.value:
                weakest_status = impact_enum
            excursions.append(
                ThermalExcursionDTO(
                    timestamp=record.timestamp,
                    temperature=record.temperature,
                    duration_minutes=record.duration_minutes,
                    impact_level=impact_str,
                )
            )

        return excursions, weakest_status.name
