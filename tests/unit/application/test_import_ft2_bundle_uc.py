# tests/unit/application/test_import_ft2_bundle_uc.py
"""Unit tests for ImportFT2BundleUseCase."""

from pathlib import Path

import pytest

from src.application.use_cases.import_ft2_bundle_uc import (
    ImportFT2BundleRequest,
    ImportFT2BundleResponse,
    ImportFT2BundleUseCase,
)
from src.domain.entities.device_identity import DeviceIdentity


class DummyRepo:
    def __init__(self):
        self.saved = []

    def save_txt(self, path, device):
        self.saved.append(("txt", path, device))
        return True

    def save_pdf(self, path, device):
        self.saved.append(("pdf", path, device))
        return True


def test_import_paths_not_exist(tmp_path):
    repo = DummyRepo()
    uc = ImportFT2BundleUseCase(repo, ledger_writer=None)
    req = ImportFT2BundleRequest(txt_path=tmp_path / "no.txt")
    resp = uc.execute(req)
    assert not resp.success
    assert "not found" in resp.error_message


def test_import_creates_device_identity(tmp_path):
    repo = DummyRepo()
    # create dummy file
    f = tmp_path / "FT2-xyz.txt"
    f.write_text("x")
    uc = ImportFT2BundleUseCase(repo, ledger_writer=None)
    req = ImportFT2BundleRequest(txt_path=f, device_id="D1", serial_number="S1")
    resp = uc.execute(req)
    assert resp.success
    assert isinstance(resp.device_identity, DeviceIdentity)
    assert resp.device_identity.device_id == "D1"
