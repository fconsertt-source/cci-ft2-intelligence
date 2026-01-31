import logging
import types

import pytest

from src import main


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
        def execute(self):
            executed["ok"] = True
            return [FakeResult()]

    def fake_factory(reader=None, repository=None):
        return FakeUC()

    monkeypatch.setattr(main, "create_evaluate_cold_chain_uc", fake_factory)

    main.main(["evaluate"])

    assert executed["ok"] is True
    assert "Running EvaluateColdChainSafetyUC" in caplog.text
    assert "Vaccine=VAX-123" in caplog.text


def test_cli_simple_pipeline_invokes_run(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    called = {"ok": False}

    def fake_run():
        logging.getLogger().info("simple-pipeline-run")
        called["ok"] = True

    import scripts.simple_pipeline as sp
    monkeypatch.setattr(sp, "run_simple_pipeline", fake_run)

    main.main(["simple-pipeline"])

    assert called.get("ok") is True
    assert "simple-pipeline-run" in caplog.text
