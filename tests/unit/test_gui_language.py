import pytest

from src.presentation.cli import gui_main
from src.shared.language_manager import LanguageManager


@pytest.fixture(autouse=True)
def reset_language_manager():
    # language manager is a singleton; clear any loaded translations between tests
    lang = LanguageManager()
    lang._translations.clear()
    lang._fallback_chain = ["ar", "en"]
    lang._current_lang = "ar"
    yield


def test_gui_initializes_with_arabic(monkeypatch):
    """GuardianGUI should load Arabic translations by default when files exist."""

    # prevent actual UI creation and avoid Tcl/Tk errors by stubbing Tk
    class DummyRoot:
        def title(self, *_):
            pass

        def geometry(self, *_):
            pass

        def protocol(self, *_):
            pass

        def config(self, **_):
            pass

    monkeypatch.setattr(gui_main.tk, "Tk", DummyRoot)
    monkeypatch.setattr(gui_main.GuardianGUI, "_build_ui", lambda self: None)

    gui = gui_main.GuardianGUI()
    assert gui.current_lang == "ar"

    # the language manager itself should report Arabic
    assert LanguageManager().current_language == "ar"

    # a known key should translate to Arabic text (we look up one
    # translation that is guaranteed to be defined in locales)
    translated = gui._get_text("menu.exit")
    assert translated != "menu.exit"
    assert "خروج" in translated or "Exit" not in translated


def test_gui_language_switch(monkeypatch):
    class DummyRoot:
        def title(self, *_):
            pass

        def geometry(self, *_):
            pass

        def protocol(self, *_):
            pass

        def config(self, **_):
            pass

    monkeypatch.setattr(gui_main.tk, "Tk", DummyRoot)
    monkeypatch.setattr(gui_main.GuardianGUI, "_build_ui", lambda self: None)
    gui = gui_main.GuardianGUI()

    # stub out UI refresh and dialogs since we're not creating full UI
    monkeypatch.setattr(gui_main.GuardianGUI, "_refresh_ui_texts", lambda self: None)
    monkeypatch.setattr(gui_main.messagebox, "showinfo", lambda *args, **kwargs: None)
    monkeypatch.setattr(gui_main.messagebox, "showerror", lambda *args, **kwargs: None)

    # switch to English; this should load the file if not already loaded
    gui._switch_lang("en")
    assert gui.current_lang == "en"
    assert LanguageManager().current_language == "en"
    assert gui._get_text("menu.exit") == "Exit"

    # switch back to Arabic again
    gui._switch_lang("ar")
    assert gui.current_lang == "ar"
    assert LanguageManager().current_language == "ar"
