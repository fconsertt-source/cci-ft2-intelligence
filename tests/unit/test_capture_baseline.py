"""Tests for the capture_golden_baseline script helpers."""

import json
import shutil
import tempfile
from pathlib import Path

from scripts.capture_golden_baseline import BASELINE_DIR, main


def test_capture_baseline_default(tmp_path, monkeypatch):
    # redirect baseline dir to temporary location
    monkeypatch.setattr("scripts.capture_golden_baseline.BASELINE_DIR", tmp_path)
    success = main(languages=["ar"])
    assert success
    # metadata file should exist
    assert (tmp_path / "golden_metadata.json").exists()


def test_capture_baseline_multiple_languages(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.capture_golden_baseline.BASELINE_DIR", tmp_path)
    success = main(languages=["ar", "en"])
    assert success
    # two report entries per strategy: official-ar etc.
    meta = json.loads((tmp_path / "golden_metadata.json").read_text())
    assert any("official-ar" in k for k in meta["reports"])
    assert any("official-en" in k for k in meta["reports"])
