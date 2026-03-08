"""Unit tests for UnifiedPDFGenerator font setup logic."""

import builtins
import os

import pytest

from src.infrastructure.pdf.unified_pdf_generator import (
    _HAS_REPORTLAB,
    UnifiedPDFGenerator,
)

# module-level skip when ReportLab (a hard requirement for the class) is missing
if not _HAS_REPORTLAB:
    pytest.skip(
        "ReportLab not available, skipping PDF font tests", allow_module_level=True
    )


class DummyFont:
    pass


def test_font_setup_fallback(monkeypatch, tmp_path):
    """When no custom fonts exist, fallback to Helvetica."""
    # ensure os.path.exists returns False for everything
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    # intercept registration to avoid needing a real ttf
    monkeypatch.setattr(
        "src.infrastructure.pdf.unified_pdf_generator.pdfmetrics.registerFont",
        lambda f: None,
    )
    monkeypatch.setattr(
        "src.infrastructure.pdf.unified_pdf_generator.TTFont",
        lambda name, path: DummyFont(),
    )

    gen = UnifiedPDFGenerator()
    assert gen.font_name == "Helvetica", "Should default when no fonts are found"


def test_font_setup_arabic_selection(monkeypatch):
    """If an Arabic font path exists, it should be chosen and named ArabicFont."""

    # Fake os.path.exists to return True only for arabic.ttf
    def fake_exists(path):
        return "arabic.ttf" in path.lower()

    monkeypatch.setattr(os.path, "exists", fake_exists)

    # Capture the registered font
    registered = {}

    def fake_register(font):
        registered["font"] = font

    monkeypatch.setattr(
        "src.infrastructure.pdf.unified_pdf_generator.pdfmetrics.registerFont",
        fake_register,
    )

    # Replace TTFont with DummyFont
    monkeypatch.setattr(
        "src.infrastructure.pdf.unified_pdf_generator.TTFont",
        lambda name, p: DummyFont(),
    )

    gen = UnifiedPDFGenerator()

    # Assertions
    assert "font" in registered, "Font key should be registered"
    font_obj = registered["font"]
    assert isinstance(font_obj, DummyFont), "Registered font should be DummyFont"
    assert (
        gen.font_name == "ArabicFont"
    ), "Generator should report font_name as ArabicFont"
