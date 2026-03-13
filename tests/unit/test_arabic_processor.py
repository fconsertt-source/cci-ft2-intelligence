import src.presentation.reporting.components.arabic_processor as mod
from src.presentation.reporting.components.arabic_processor import shape


def test_shape_no_libs(monkeypatch):
    # simulate missing libraries
    monkeypatch.setattr(mod, "ARABIC_LIBS_AVAILABLE", False)
    assert shape("مرحبا") == "مرحبا"


def test_shape_with_libs(monkeypatch):
    # if libs available but shaping fails, return input
    monkeypatch.setattr(mod, "ARABIC_LIBS_AVAILABLE", True)

    def fake_reshaper(s):
        raise ValueError("fail")

    monkeypatch.setattr(
        mod,
        "arabic_reshaper",
        type("X", (), {"reshape": fake_reshaper}),
        raising=False,
    )
    assert shape("سلام") == "سلام"
