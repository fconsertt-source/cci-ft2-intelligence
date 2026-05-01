#!/usr/bin/env python3
"""PDF report strategy interfaces used throughout the application.
Defines a simple abstract base class that each client-facing strategy must
implement. Concrete strategy classes delegate to the legacy generator wrapper
so the rest of the codebase does not depend directly on the old implementation.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

# Import the single, unified generator factory
from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import \
    get_pdf_generator

if TYPE_CHECKING:
    from src.application.dtos.device_report_dto import DeviceReportDTO


class PDFReportStrategy(ABC):
    """Unified interface for all PDF report creation strategies."""

    @abstractmethod
    def generate(
        self,
        dto: "DeviceReportDTO",
        filename: Optional[str] = None,
        language: str = "ar",
    ) -> bytes:
        """Generate PDF bytes from a domain DTO.
        Subclasses should implement this method.
        """
        pass


class OfficialPDFStrategy(PDFReportStrategy):
    """Official report style (signatures, headers, etc.)."""

    def __init__(self, language: str = "ar"):
        # language parameter is accepted for backwards compatibility; the
        # underlying factory is a singleton so only the first call matters.
        self.generator = get_pdf_generator(language=language)

    def generate(
        self,
        dto: "DeviceReportDTO",
        filename: Optional[str] = None,
        language: str = "ar",
    ) -> bytes:
        # The unified wrapper has a `render` method that handles all logic.
        return self.generator.render(dto, force_report_type="official")


class TechnicalPDFStrategy(PDFReportStrategy):
    """Technical report style with charts and tables."""

    def __init__(self, language: str = "ar"):
        self.generator = get_pdf_generator(language=language)

    def generate(
        self,
        dto: "DeviceReportDTO",
        filename: Optional[str] = None,
        language: str = "ar",
    ) -> bytes:
        return self.generator.render(dto, force_report_type="technical")


class ArabicPDFStrategy(PDFReportStrategy):
    """استراتيجية توليد التقارير بالعربية"""

    def __init__(self):
        self._generator = None

    @property
    def generator(self):
        """Return underlying wrapper instance (for tests/legacy callers)."""
        if self._generator is None:
            # default language is Arabic
            self._generator = self.get_pdf_generator()
        return self._generator

    def generate(
        self,
        dto: "DeviceReportDTO",
        filename: Optional[str] = None,
        language: str = "ar",
    ) -> bytes:
        """توليد تقرير PDF بالعربية"""
        if self._generator is None:
            self._generator = self.get_pdf_generator(language)
        return self._generator.render(dto, force_report_type="arabic")

    def get_pdf_generator(self, language: str = "ar"):
        """Return the PDF generator used by this strategy.

        The ``language`` argument is accepted for compatibility and forwarded to
        the factory; the underlying singleton means that only the first call
        can influence the instance created.
        """
        from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import \
            get_pdf_generator

        return get_pdf_generator(language=language)
