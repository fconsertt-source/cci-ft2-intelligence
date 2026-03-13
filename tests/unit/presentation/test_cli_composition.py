# tests/unit/presentation/test_cli_composition.py
"""Ensure the CLI uses AppComposer for building use cases."""

import pytest

try:
    from src.presentation.cli import cli
except ImportError:
    cli = None
from src.application.app_composer import AppComposer


def test_cli_import_uses_composer(monkeypatch, tmp_path):
    if cli is None:
        pytest.skip("typer not installed, skipping CLI tests")

    # prepare dummy file
    p = tmp_path / "ft2.txt"
    p.write_text("x")
    called = {}

    class DummyUC:
        def execute(self, input_dir, output_path):
            called["imported"] = True

    monkeypatch.setattr(
        AppComposer, "create_import_ft2_bundle_uc", staticmethod(lambda: DummyUC())
    )

    # simulate command invocation directly
    runner = cli.app.test_cli_runner()
    result = runner.invoke(
        cli.app,
        [
            "import-data",
            "--input",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.json"),
        ],
    )
    assert result.exit_code == 0
    assert called.get("imported", False)
