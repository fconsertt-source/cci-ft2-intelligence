from __future__ import annotations
from src.application.security.license_guard import LicenseGuard

from typing import List, Optional
from pathlib import Path

from src.application.ports.device_repository_port import DeviceRepositoryPort
from src.application.ports.vaccine_specification_port import VaccineSpecificationPort
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import ThermalDegradationEstimator
from src.application.ports.validation_protocol_port import ValidationProtocolPort
from src.application.dtos.device_report_dto import DeviceReportDTO, ThermalExcursionDTO
from src.domain.entities.thermal_record import ThermalRecord
from src.domain.enums.regulatory_status import RegulatoryStatus


class GenerateDeviceReportUseCase:
    """
    Orchestrates device-level thermal accountability with ETHICAL BOUNDARIES.

    Responsibilities:
      • Retrieve immutable device timeline
      • Fetch vaccine-specific specification
      • Delegate evaluation to REGULATORY engine (binary decisions only)
      • Apply weakest-link principle
      • Provide ADVISORY section separately
      • Enforce validation protocols for PARTIAL status

    Non-responsibilities:
      • No probabilistic models in decision path
      • No advisory calculations in decision path
      • No infrastructure interaction
    """

    def __init__(
        self,
        device_repository: DeviceRepositoryPort,
        vaccine_specifications: VaccineSpecificationPort,
        regulatory_decision_service: RegulatoryDecisionService,  # ← Regulatory engine only
        estimator: ThermalDegradationEstimator,               # ← Advisory only (separate path)
        validator: ValidationProtocolPort,                    # ← Validation enforcement
        license_guard: LicenseGuard,
        data_path: Optional[Path] = None,  # ✅ إضافة data_path كمعامل اختياري
    ):
        self._repo = device_repository
        self._specs = vaccine_specifications
        self._regulatory_decision = regulatory_decision_service  # ← Decision engine
        self._estimator = estimator                            # ← Advisory only
        self._validator = validator                           # ← Validation enforcement
        self._guard = license_guard
        self._data_path = data_path  # ✅ حفظ data_path

    def execute(self, device_id: str) -> DeviceReportDTO:
        # 🔒 Guard first — before any domain logic
        self._guard.ensure_active()  # ← يرفع استثناءً إذا كان EXPIRED/TAMPERED

        records = self._retrieve_device_timeline(device_id)
        spec = self._fetch_vaccine_specification(records)
        
        # 1️⃣ Regulatory evaluation (BINARY decisions only) - COMPLETELY INDEPENDENT
        excursions, final_status = self._evaluate_timeline_regulatory(records, spec)
        
        # 2️⃣ Advisory calculation (SEPARATE path - NO decision influence)
        # ← Happens AFTER final_status is determined
        advisory_info = self._estimator.calculate_cumulative_impact(
            thermal_history=records,
            spec=spec
        )
        
        # 3️⃣ Validation enforcement
        validation_required = None
        if final_status == "PARTIAL":
            validation_required = self._validator.get_protocol(spec.vaccine_type)

        return DeviceReportDTO(
            device_id=device_id,
            vaccine_type=spec.vaccine_type,
            total_records=len(records),
            excursions=excursions,
            final_status=final_status,
            scientific_rationale=spec.rationale,
            advisory_section=advisory_info,      # ← Separate advisory section
            validation_required=validation_required  # ← Validation enforced
        )

    def _retrieve_device_timeline(self, device_id: str) -> List[ThermalRecord]:
        records = self._repo.get_device_history(device_id)
        if not records:
            raise ValueError(f"No thermal history found for device: {device_id}")
        return records

    def _fetch_vaccine_specification(self, records: List[ThermalRecord]) -> 'VaccineSpecification':
        vaccine_type = records[0].vaccine_type
        return self._specs.get_spec(vaccine_type)

    def _evaluate_timeline_regulatory(
        self,
        records: List[ThermalRecord],
        spec: 'VaccineSpecification',
    ) -> tuple[List[ThermalExcursionDTO], str]:
        """
        Evaluate timeline using REGULATORY thresholds only.
        NO probabilistic models allowed.
        NO estimator calls allowed.
        """
        excursions: List[ThermalExcursionDTO] = []
        weakest_status = RegulatoryStatus.SAFE

        # status_priority = {"DISCARD": 2, "PARTIAL": 1, "SAFE": 0}
        # Use enum values for safety
        for record in records:
            # ← Regulatory decision only (binary) - NO ESTIMATOR INVOLVED
            impact_str = self._regulatory_decision.evaluate(
                temperature=record.temperature,
                duration_minutes=record.duration_minutes,
                spec=spec,
            )
            
            impact_enum = getattr(RegulatoryStatus, impact_str, RegulatoryStatus.SAFE)
            
            # Apply weakest-link principle using enum values
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
