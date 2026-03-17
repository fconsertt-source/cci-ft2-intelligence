import logging
import sys
import types
from pathlib import Path

# إضافة المسار للوصول إلى main
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.application.app_composer import AppComposer
from src.presentation.cli import cli as main


def test_cli_evaluate_logs_results(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    executed = {"ok": False}

    class FakeResult:
        def __init__(self):
            self.vaccine_id = "VAX-123"
            self.status = types.SimpleNamespace(value="OK")
            self.alert_level = "LOW"
            self.her = 0.123
            self.ccm = 4.56
            self.recommendations = ["Keep cold chain"]

    class FakeUC:
        def execute(self, request):
            executed["ok"] = True
            return [FakeResult()]

    def fake_factory():
        return FakeUC()

    monkeypatch.setattr(AppComposer, "create_evaluate_cold_chain_uc", fake_factory)

    # محاكاة استدعاء CLI مع وسيط evaluate
    test_args = ["ft2-cli", "evaluate", "--center", "test-center"]
    monkeypatch.setattr(sys, "argv", test_args)

    # تنفيذ الأمر
    try:
        main.app()
    except SystemExit:
        pass

    assert executed["ok"] is True


def test_cli_simple_pipeline_invokes_run(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    called = {"ok": False}

    def fake_run():
        logging.getLogger().info("simple-pipeline-run")
        called["ok"] = True

    import scripts.simple_pipeline as sp
    monkeypatch.setattr(sp, "run_simple_pipeline", fake_run)

    # محاكاة استدعاء CLI مع وسيط simple-pipeline
    test_args = ["ft2-cli", "simple-pipeline"]
    monkeypatch.setattr(sys, "argv", test_args)

    try:
        main.app()
    except SystemExit:
        pass

    assert called.get("ok") is True
    assert "simple-pipeline-run" in caplog.text


def test_cli_health_check(monkeypatch):
    """اختبار أمر health_check"""
    health_checked = {"ok": False}

    def fake_health_check():
        health_checked["ok"] = True
        return True

    monkeypatch.setattr(AppComposer, "health_check", fake_health_check)

    test_args = ["ft2-cli", "health-check"]
    monkeypatch.setattr(sys, "argv", test_args)

    try:
        main.app()
    except SystemExit:
        pass

    assert health_checked["ok"] is True
