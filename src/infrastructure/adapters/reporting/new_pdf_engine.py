# src/infrastructure/adapters/reporting/new_pdf_engine.py
"""Modular replacement for UnifiedPDFGenerator."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.application.dtos.device_report_dto import DeviceReportDTO
from src.application.ports.i_pdf_report_generator import IPDFReportGenerator

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class PDFGenerator(IPDFReportGenerator):
    """المحرك الرئيسي لتوليد التقارير عبر WeasyPrint."""

    def __init__(self, language: str = "ar", theme_color: str = "blue") -> None:
        self.language = language
        self.theme_color = theme_color
        self.font_name = "Tajawal"

    def generate_device_report_pdf(
        self,
        dto: DeviceReportDTO,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None,
    ) -> bytes:
        return self.generate(dto, report_type, language)

    def generate_center_report_pdf(
        self,
        center_data: dict,
        report_type: str = "official",
        language: str = "ar",
        filename: Optional[str] = None,
    ) -> bytes:
        logger.warning("Center report generation not fully implemented yet")
        return b""

    def generate(
        self,
        dto: Any,
        report_type: str = "official",
        language: Optional[str] = None,
    ) -> bytes:
        """نقطة الدخول الرئيسية: تحويل DTO إلى PDF باستخدام WeasyPrint."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint library is required for PDF generation")

        lang = language or self.language
        try:
            from src.presentation.reporting.professional.professional_vaccine_report import (
                ProfessionalVaccineReport,
            )
        except ImportError:
            logger.exception("Failed to import ProfessionalVaccineReport")
            raise

        report = ProfessionalVaccineReport()
        context = self._build_context(dto, report_type=report_type, language=lang)
        readings = getattr(dto, "readings", [])

        try:
            # ✅ استدعاء render_vaccine_a4 مباشرة — لا وجود لـ prepare_elements
            return report.render_vaccine_a4(context, readings=readings)
        except Exception:
            logger.exception("Critical failure in WeasyPrint PDF generation")
            raise

    def _build_context(self, dto: Any, report_type: str, language: str) -> dict:
        generated_at = getattr(dto, "generated_at", None)
        if isinstance(generated_at, datetime):
            generated_at = generated_at.strftime("%Y-%m-%d %H:%M:%S")
        elif generated_at is None:
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            generated_at = str(generated_at)

        final_status = getattr(dto, "final_status", "")
        if isinstance(final_status, str):
            final_status = final_status.lower()
        elif hasattr(final_status, "value"):
            final_status = str(final_status.value).lower()
        else:
            final_status = str(final_status).lower()

        if not final_status:
            decision = getattr(dto, "decision", "")
            final_status = (
                str(decision.value).lower()
                if hasattr(decision, "value")
                else str(decision).lower()
            )

        summary = {
            "total": max(1, int(getattr(dto, "total_records", 1) or 1)),
            "safe": 1 if final_status == "safe" else 0,
            "warning": 1 if final_status == "warning" else 0,
            "discard": 1 if final_status == "discard" else 0,
        }

        temperature_ranges = getattr(dto, "temperature_ranges", {}) or {}

        return {
            "language": language,
            "report_id": getattr(dto, "device_id", "UNKNOWN").replace(" ", "_").upper(),
            "generated_at": generated_at,
            "subtitle": getattr(dto, "scientific_rationale", ""),
            "device_id": getattr(dto, "device_id", "-"),
            "center_name": getattr(dto, "center_name", "-"),
            "equipment_type": getattr(dto, "equipment_type", "-"),
            "vaccine_type": getattr(dto, "vaccine_type", "-"),
            "temp_min": temperature_ranges.get("min", "-"),
            "temp_max": temperature_ranges.get("max", "-"),
            "exposure_minutes": getattr(dto, "stats", {}).get("exposure_minutes", 0),
            "category_display": getattr(dto, "advisory_section", {}).get("category_display", "-"),
            "stability_budget_consumed_pct": float(
                getattr(dto, "stability_budget_consumed_pct", 0.0) or 0.0
            ),
            "supervisor_name": getattr(dto, "operator", "-"),
            "municipality": getattr(dto, "municipality", "-"),
            "decision": getattr(dto, "decision", ""),
            "vvm_stage": getattr(dto, "vvm_stage", ""),
            "summary": summary,
        }