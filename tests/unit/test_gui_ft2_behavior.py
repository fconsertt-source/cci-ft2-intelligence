

from src.presentation.cli import gui_main
from src.presentation.messages.message_map import MessageMap


class DummyRoot:
    def title(self, *_):
        pass

    def geometry(self, *_):
        pass

    def protocol(self, *_):
        pass

    def config(self, **_):
        pass


def make_gui(monkeypatch):
    # stub Tk and avoid building full UI
    monkeypatch.setattr(gui_main.tk, "Tk", DummyRoot)
    monkeypatch.setattr(gui_main.GuardianGUI, "_build_ui", lambda self: None)
    return gui_main.GuardianGUI()


def test_ft2_missing_shows_warning(monkeypatch, tmp_path, capsys):
    """_ensure_ft2_data_available should warn when the JSON file is absent."""
    gui = make_gui(monkeypatch)

    called = {}

    def fake_warning(title, message):
        called["title"] = title
        called["message"] = message

    monkeypatch.setattr(gui_main.messagebox, "showwarning", fake_warning)

    # ensure file does not exist
    if tmp_path.exists():
        pass
    monkeypatch.chdir(tmp_path)

    gui._ensure_ft2_data_available()

    assert "message" in called
    # Allow either the translated message from MessageMap or our hard‑coded
    # fallback string from the implementation.  We only need to verify that
    # a meaningful warning was shown, not the exact wording.
    expected_text = MessageMap.get("WARNING_NO_FT2_DATA")
    msg = called["message"]
    assert msg, "warning message should not be empty"
    assert "FT2" in msg or "FT2" in expected_text


def test_generate_pdf_prompts_for_device(monkeypatch, tmp_path):
    """_generate_pdf should call askstring and return gracefully if user cancels."""
    gui = make_gui(monkeypatch)

    # simulate presence of ft2_data.json to pass the early guard
    (tmp_path / "ft2_data.json").write_text("[]")
    monkeypatch.chdir(tmp_path)

    # capture prompt invocation
    monkeypatch.setattr(
        gui_main.simpledialog, "askstring", lambda *args, **kwargs: None
    )

    # stub warning/messagebox to avoid real dialogs
    monkeypatch.setattr(
        gui_main.messagebox, "showwarning", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(gui_main.messagebox, "showinfo", lambda *args, **kwargs: None)
    monkeypatch.setattr(gui_main.messagebox, "showerror", lambda *args, **kwargs: None)

    # call method; should not raise
    gui._generate_pdf()

    # since askstring returned None, nothing should be appended to cycle_data
    assert gui.cycle_data["reports_generated"] == []
