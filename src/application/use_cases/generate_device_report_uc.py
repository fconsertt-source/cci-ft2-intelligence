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
from src.application.ports.validation_protocol_port import \
    ValidationProtocolPort
from src.application.security.license_guard import LicenseGuard
from src.application.use_cases.requests import GenerateDeviceReportRequest
from src.domain.dtos.device_report_dto import (DeviceReportDTO,
                                               ThermalExcursionDTO)
from src.domain.entities.thermal_record import ThermalRecord
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.enums.regulatory_status import RegulatoryStatus
from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator
from src.domain.value_objects.vaccine_specification import get_vaccine_spec


class GenerateDeviceReportUseCase:
    """
    حالة استخدام توليد تقرير الجهاز الحراري

    الإصدار: 2.0
    التحديث: استخدام vaccine_library.yaml كمصدر مركزي للمواصفات
    """

    def __init__(
        self,
        device_repository: DeviceRepositoryPort,
        vaccine_specifications: Optional[VaccineSpecificationPort] = None,
        regulatory_decision_service: Optional[RegulatoryDecisionService] = None,
        estimator: Optional[ThermalDegradationEstimator] = None,
        exposure_analysis: Optional[ExposureAnalysisService] = None,
        validator: Optional[ValidationProtocolPort] = None,
        license_guard: Optional[LicenseGuard] = None,
        ledger_writer: Optional[LedgerWriterPort] = None,
        data_path: Optional[Path] = None,
        yaml_path: Optional[Path] = None,
    ):
        self._repo = device_repository
        self._specs = vaccine_specifications
        self._regulatory_decision = regulatory_decision_service
        self._estimator = estimator
        self._exposure_analysis = exposure_analysis or ExposureAnalysisService()
        self._validator = validator
        self._guard = license_guard
        self._ledger_writer = ledger_writer
        self._data_path = data_path or Path("data")
        self._yaml_path = yaml_path or Path("config/vaccine_library.yaml")

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

        if self._guard:
            self._guard.ensure_active()

        if self._ledger_writer:
            self._ledger_writer.append(
                event_type=str(LedgerEvent.OPERATOR_SESSION_STARTED),
                operator=request.operator,
                file_hash="N/A",
                ft2_serial=request.device_id,
                cycle_id=request.cycle_id,
            )

        # ✅ 1. استرجاع السجلات أولاً
        records = self._retrieve_device_timeline(
            request.device_id, request.date_from, request.date_to
        )

        # ✅ 2. جلب مواصفات اللقاح
        spec = self._fetch_vaccine_specification(records)

        # ✅ 3. تحليل CCM و HER (بعد توفر records و spec)
        ccm_index = "0"
        her_ratio = 0.0
        if self._exposure_analysis and records:
            analysis = self._exposure_analysis.analyze(records, spec)
            ccm_index = analysis.get("ccm_index", "0")
            her_ratio = analysis.get("her_ratio", 0.0)

        # ✅ 4. تقييم الرحلات الحرارية
        excursions, final_status = self._evaluate_timeline_regulatory(records, spec)

        advisory_info = None
        if self._estimator:
            advisory_info = self._estimator.calculate_cumulative_impact(
                thermal_history=records, spec=spec
            )

        validation_required = None
        if final_status == RegulatoryStatus.PARTIAL.name and self._validator:
            validation_required = self._validator.get_protocol(spec.vaccine_type)

        # ✅ 5. إنشاء التقرير مع إضافة CCM و HER
        report = DeviceReportDTO(
            device_id=request.device_id,
            vaccine_type=spec.vaccine_type,
            total_records=len(records),
            excursions=excursions,
            final_status=final_status,
            scientific_rationale=getattr(spec, "reference", "WHO/IVB/06.10"),
            advisory_section=advisory_info,
            validation_required=validation_required,
            operator=request.operator,
            cycle_id=request.cycle_id,
            ccm_index=ccm_index,  # ✅ إضافة CCM index
            her_percentage=her_ratio * 100 if her_ratio else 0.0,  # ✅ إضافة HER
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
            if date_from is None and date_to is None:
                records = self._repo.get_device_history(device_id)
            else:
                records = self._repo.get_device_history(
                    device_id, date_from=date_from, date_to=date_to
                )
        except TypeError:
            records = self._repo.get_device_history(device_id)

        if not records:
            error_msg = f"No thermal history found for device: {device_id}"
            if date_from or date_to:
                error_msg += " within the specified date range."
            raise ValueError(error_msg)

        return records

    def _fetch_vaccine_specification(self, records: List[ThermalRecord]) -> Any:
        """
        جلب مواصفات اللقاح من vaccine_library.yaml

        الأولويات:
        1. من VaccineSpecificationPort إذا وُجد
        2. من vaccine_type في السجلات
        3. Fallback إلى GENERAL
        """
        # ✅ الأولوية: استخدام VaccineSpecificationPort إذا وُجد
        if self._specs:
            try:
                vaccine_type = records[0].vaccine_type if records else "GENERAL"
                spec = self._specs.get_spec(vaccine_type)
                if spec:
                    return spec
            except Exception:
                pass

        # ✅ Fallback: استخدام vaccine_library.yaml مباشرة
        vaccine_type = records[0].vaccine_type if records else "GENERAL"
        return get_vaccine_spec(vaccine_type)

    def _evaluate_timeline_regulatory(
        self, records: List[ThermalRecord], spec: Any
    ) -> Tuple[List[ThermalExcursionDTO], str]:
        excursions: List[ThermalExcursionDTO] = []
        weakest_status = RegulatoryStatus.SAFE

        for record in records:
            if self._regulatory_decision:
                impact_str = self._regulatory_decision.evaluate(
                    temperature=record.temperature,
                    duration_minutes=record.duration_minutes,
                    spec=spec,
                )
            else:
                # Fallback: تقييم بسيط إذا لم تكن الخدمة متوفرة
                impact_str = "SAFE"
                if record.temperature < -0.5:
                    impact_str = "PARTIAL"
                elif record.temperature > 34.0:
                    impact_str = "DISCARD"

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

    def reload_vaccine_library(self) -> None:
        """
        إعادة تحميل مكتبة اللقاحات من YAML
        (مفيد عند تحديث الملف بدون إعادة تشغيل التطبيق)
        """
        from src.domain.value_objects.vaccine_specification import \
            reload_vaccine_library

        reload_vaccine_library(self._yaml_path)

    def get_vaccine_library_info(self) -> dict:
        """
        الحصول على معلومات مكتبة اللقاحات

        Returns:
            dict: معلومات عن المكتبة (عدد اللقاحات، المسار، آخر تحديث)
        """
        from src.domain.value_objects.vaccine_specification import (
            _YAML_PATH, _load_vaccine_library)

        catalogue = _load_vaccine_library(self._yaml_path)

        return {
            "total_vaccines": len(catalogue),
            "yaml_path": str(_YAML_PATH or self._yaml_path),
            "freeze_sensitive_count": len(
                [v for v in catalogue.values() if v.freeze_sensitive]
            ),
            "freeze_stable_count": len(
                [v for v in catalogue.values() if not v.freeze_sensitive]
            ),
        }
