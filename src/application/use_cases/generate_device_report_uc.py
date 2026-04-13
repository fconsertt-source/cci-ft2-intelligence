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
from src.application.ports.vaccine_specification_port import \
    VaccineSpecificationPort
from src.application.ports.validation_protocol_port import ValidationProtocolPort
from src.application.ports.i_license_guard import ILicenseGuard
from src.infrastructure.utils.config_loader import ConfigLoader
from src.application.use_cases.requests import GenerateDeviceReportRequest
from src.application.dtos import DeviceReportDTO, ThermalExcursionDTO
from src.application.dtos.device_report_dto import ReportDecision, VVMStage
from src.domain.entities.thermal_record import ThermalRecord
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.enums.regulatory_status import RegulatoryStatus
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator

_DEFAULT_SHELF_LIFE_HOURS = 730 * 24  # سنتان


class GenerateDeviceReportUseCase:
    def __init__(
        self,
        device_repository: DeviceRepositoryPort,
        vaccine_specifications: VaccineSpecificationPort,
        regulatory_decision_service: RegulatoryDecisionService,
        estimator: ThermalDegradationEstimator,
        validator: ValidationProtocolPort,
        license_guard: ILicenseGuard,
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
        if not isinstance(request, GenerateDeviceReportRequest):
            device_id = kwargs.get("device_id") or request
            if not device_id:
                raise TypeError(
                    "execute() requires a request object or a device_id argument"
                )
            request = GenerateDeviceReportRequest(device_id=device_id)

        self._guard.ensure_active()

        if self._ledger_writer:
            self._ledger_writer.append(
                event_type=str(LedgerEvent.OPERATOR_SESSION_STARTED),
                operator=request.operator,
                file_hash="N/A",
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

        # ✅ تحويل نتيجة calculate_cumulative_impact إلى dict آمن
        if not isinstance(advisory_info, dict):
            advisory_info = {}

        required_shelf_life_pct = ConfigLoader.get(
            "thresholds.remaining_shelf_life_percentage", 50
        )
        remaining_pct = advisory_info.get("remaining_shelf_life", 0.0)
        if not isinstance(remaining_pct, (int, float)):
            remaining_pct = 0.0

        advisory_info["remaining_shelf_life_threshold"] = required_shelf_life_pct
        advisory_info["remaining_shelf_life_ok"] = remaining_pct >= required_shelf_life_pct

        validation_required = None
        if final_status == RegulatoryStatus.PARTIAL.name and self._validator:
            validation_required = self._validator.get_protocol(spec.vaccine_type)

        decision_mapping = {
            "SAFE": ReportDecision.SAFE,
            "PARTIAL": ReportDecision.PARTIAL,
            "DISCARD": ReportDecision.REJECTED_HEAT_C,
        }
        decision = decision_mapping.get(final_status, ReportDecision.UNKNOWN)

        if records:
            temperatures = [r.temperature for r in records]
            temperature_ranges = {
                "min": min(temperatures),
                "max": max(temperatures),
            }
        else:
            temperature_ranges = {"min": 0.0, "max": 0.0}

        prelim_hash = hashlib.sha256(
            json.dumps(
                {
                    "device_id": request.device_id,
                    "final_status": final_status,
                    "generated_at": datetime.now().isoformat(),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        decision_reasons = [spec.rationale] if spec.rationale else []
        if not advisory_info.get("remaining_shelf_life_ok", True):
            decision_reasons.append(
                f"Estimated remaining shelf life {remaining_pct:.1f}% "
                f"below recommended {required_shelf_life_pct}% at delivery"
            )

        # ✅ استخراج shelf_life_hours بأمان — يمنع float * Mock
        raw_shelf_life = getattr(spec, "shelf_life_hours", None)
        if isinstance(raw_shelf_life, (int, float)) and raw_shelf_life > 0:
            total_shelf_life_hours = float(raw_shelf_life)
        else:
            total_shelf_life_hours = float(_DEFAULT_SHELF_LIFE_HOURS)

        thaw_remaining_hours = (remaining_pct / 100.0) * total_shelf_life_hours

        # ✅ cumulative_impact آمن
        raw_impact = advisory_info.get("cumulative_impact", 0.0)
        if not isinstance(raw_impact, (int, float)):
            raw_impact = 0.0
        stability_pct = min(
            max(
                (raw_impact / 100.0 if raw_impact > 1.0 else raw_impact) * 100,
                0.0,
            ),
            100.0,
        )

        report = DeviceReportDTO(
            device_id=request.device_id,
            center_id=f"CTR_{request.device_id}",
            center_name=f"Center for {request.device_id}",
            temperature_ranges=temperature_ranges,
            decision=decision,
            vvm_stage=VVMStage.A,
            alert_level=final_status,
            stability_budget_consumed_pct=stability_pct,
            thaw_remaining_hours=thaw_remaining_hours,
            aefi_reporting_required=any(
                exc.aefi_report_recommended for exc in excursions
            ),
            flexible_vvm_policy_applied=(
                ConfigLoader.get("thresholds.flexible_vvm_allowed", False)
                and spec.vaccine_type.upper() == "OPV"
            ),
            remaining_shelf_life_ok=advisory_info.get("remaining_shelf_life_ok", True),
            decision_reasons=decision_reasons,
            readings=[
                {
                    "timestamp": str(r.timestamp),
                    "temperature": r.temperature,
                    "duration": r.duration_minutes,
                }
                for r in records
            ],
            stats={
                "total_records": len(records),
                "excursions_count": len(excursions),
                "vaccine_type": spec.vaccine_type,
                "operator": request.operator,
                "cycle_id": request.cycle_id,
                "validation_required": validation_required is not None,
            },
            # Legacy fields
            vaccine_type=spec.vaccine_type,
            total_records=len(records),
            excursions=excursions,
            final_status=final_status,
            scientific_rationale=spec.rationale,
            advisory_section=advisory_info,
            validation_required=validation_required,
            operator=request.operator,
            cycle_id=request.cycle_id,
            ledger_hash=prelim_hash,
        )

        if self._ledger_writer:
            report_hash = hashlib.sha256(
                json.dumps(
                    {
                        "device_id": request.device_id,
                        "final_status": final_status,
                        "generated_at": report.generated_at.isoformat(),
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
            if date_from is None and date_to is None:
                records = self._repo.get_device_history(device_id)
            else:
                records = self._repo.get_device_history(
                    device_id, date_from=date_from, date_to=date_to
                )
        except TypeError:
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

            # السجلات الآمنة لا تُضاف إلى قائمة الانحرافات
            if impact_enum == RegulatoryStatus.SAFE:
                continue

            if record.temperature <= 0.0:
                excursion_type = "FREEZE"
                min_temperature = record.temperature
                max_temperature = None
            else:
                excursion_type = "HEAT"
                max_temperature = record.temperature
                min_temperature = None

            excursions.append(
                ThermalExcursionDTO(
                    device_id=record.device_id if hasattr(record, "device_id") else "UNKNOWN",
                    excursion_type=excursion_type,
                    duration_minutes=record.duration_minutes,
                    max_temperature=max_temperature,
                    min_temperature=min_temperature,
                    timestamp=(
                        record.timestamp.isoformat()
                        if hasattr(record.timestamp, "isoformat")
                        else str(record.timestamp)
                    ),
                    impact_level=impact_str,
                    aefi_report_recommended=(impact_str in ("DISCARD", "PARTIAL")),
                )
            )

        return excursions, weakest_status.name