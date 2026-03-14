# tests/unit/presentation/test_gui_composition.py
"""Ensure the GUI uses AppComposer rather than manual DI."""
import pytest

from src.presentation.cli import gui_main


def _display_available() -> bool:
    try:
        import tkinter

        tkinter.Tk().destroy()
        return True
    except Exception:
        return False


def test_gui_has_composer_available():
    assert hasattr(gui_main, "AppComposer"), "AppComposer should be imported"
    assert (
        gui_main.COMPOSER_AVAILABLE
    ), "COMPOSER_AVAILABLE should be True in test environment"


@pytest.mark.skipif(
    not _display_available(), reason="No display available (headless environment)"
)
def test_gui_generates_use_case_via_composer(monkeypatch):
    # Monkeypatch the composer to track call
    called = {}

    class DummyUC:
        pass

    def fake_create():
        called["called"] = True
        return DummyUC()

    monkeypatch.setattr(
        gui_main.AppComposer,
        "create_generate_device_report_uc",
        staticmethod(fake_create),
    )

    gui = gui_main.GuardianGUI()  # noqa: F841
    use_case = gui_main.AppComposer.create_generate_device_report_uc()
    assert called.get("called", False)
    assert isinstance(use_case, DummyUC)
