#!/usr/bin/env python3
"""
Production Build Readiness Gate v2.1
Guardian FT2 Intelligence

Exit codes:
    0 = READY
    1 = READY_WITH_WARNINGS
    2 = BLOCKED
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, List


# ─────────────────────────────────────────────────────────────
# 🔧 Robust project root resolution (PyInstaller / Windows / CI)
# ─────────────────────────────────────────────────────────────
def _ensure_project_on_path() -> None:
    """
    Robustly ensure the project root (containing 'src') is on sys.path.
    Works in:
    - local dev
    - CI
    - Windows bundle
    - PyInstaller
    """
    try:
        import src  # noqa: F401

        return
    except Exception:
        pass

    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "src").is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return

    cwd = Path.cwd()
    if (cwd / "src").is_dir():
        if str(cwd) not in sys.path:
            sys.path.insert(0, str(cwd))
        return

    raise RuntimeError("Unable to locate project root containing 'src' directory.")


_ensure_project_on_path()


# =========================
# Data model
# =========================
@dataclass
class GateResult:
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    def exit_code(self) -> int:
        if self.blockers:
            return 2
        if self.warnings:
            return 1
        return 0

    def status(self) -> str:
        if self.blockers:
            return "BLOCKED"
        if self.warnings:
            return "READY_WITH_WARNINGS"
        return "READY"


# =========================
# JSON deep walker
# =========================
def _walk_json_keys(obj: Any, path: str = "") -> Generator[tuple, None, None]:
    """Deep walk JSON keys recursively."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_path = f"{path}.{k}" if path else k
            yield full_path, k
            yield from _walk_json_keys(v, full_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _walk_json_keys(item, f"{path}[{i}]")


# =========================
# Checks configuration
# =========================
CRITICAL_IMPORTS = [
    "src.shared.language_manager",
    "src.application.dtos.device_report_dto",
    "src.domain.enums.ledger_event",
    "src.application.use_cases.generate_device_report_uc",
]

REQUIRED_LEDGER_EVENTS = [
    "FILE_INGESTED",
    "FILE_CORRUPTED",
    "PRE_VALIDATION_PASSED",
    "PRE_VALIDATION_FAILED",
    "AUTHENTICITY_VERIFIED",
    "AUTHENTICITY_FAILED",
    "ARCHIVE_VERIFIED",
    "ARCHIVE_VERIFY_FAILED",
    "REPORT_GENERATED",
    "OPERATOR_SESSION_STARTED",
]


# =========================
# Checks
# =========================
def check_imports(result: GateResult) -> None:
    for module in CRITICAL_IMPORTS:
        try:
            importlib.import_module(module)
        except Exception as e:
            result.blockers.append(f"Import failed: {module} → {e}")


def check_ledger_enum(result: GateResult) -> None:
    try:
        from src.domain.enums.ledger_event import LedgerEvent

        for name in REQUIRED_LEDGER_EVENTS:
            if not hasattr(LedgerEvent, name):
                result.blockers.append(f"Missing LedgerEvent: {name}")
        event_count = len(list(LedgerEvent))
        if event_count < 50:
            result.warnings.append(
                f"LedgerEvent has only {event_count} events (expected 50+)"
            )
    except Exception as e:
        result.blockers.append(f"LedgerEvent validation failed: {e}")


def check_dto_invariants(result: GateResult) -> None:
    try:
        from src.domain.dtos.device_report_dto import DeviceReportDTO

        dto = DeviceReportDTO(
            device_id="GATE-TEST",
            vaccine_type="Test",
            total_records=1,
            excursions=[],
            final_status="SAFE",
            scientific_rationale="Gate test",
        )
        if dto.generated_at is None:
            result.blockers.append("DTO generated_at missing")
        if not hasattr(dto, "operator"):
            result.blockers.append("DTO missing operator")
        if not hasattr(dto, "cycle_id"):
            result.blockers.append("DTO missing cycle_id")
    except Exception as e:
        result.blockers.append(f"DTO validation failed: {e}")


def check_json_messages(result: GateResult) -> None:
    """Deep validation of translation JSON files."""
    files = [
        "translations/ar/messages.json",
        "translations/en/messages.json",
    ]
    for lang_file in files:
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for full_path, key in _walk_json_keys(data):
                if key != key.strip():
                    result.blockers.append(
                        f"JSON key has whitespace: '{full_path}' in {lang_file}"
                    )
        except FileNotFoundError:
            result.blockers.append(f"Missing translation file: {lang_file}")
        except json.JSONDecodeError as e:
            result.blockers.append(f"Invalid JSON in {lang_file}: {e}")
        except Exception as e:
            result.blockers.append(f"Failed to validate {lang_file}: {e}")


def run_pytest(result: GateResult, max_failures: int = 0) -> None:
    try:
        proc = subprocess.run(
            ["pytest", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            match = re.search(r"(\d+)\s+failed", output)
            failed_count = int(match.group(1)) if match else 1
            if failed_count > max_failures:
                result.blockers.append(
                    f"{failed_count} test(s) failed (max allowed: {max_failures})"
                )
        match_skip = re.search(r"(\d+)\s+skipped", output, re.IGNORECASE)
        if match_skip:
            result.warnings.append(
                f"There are {int(match_skip.group(1))} skipped tests"
            )
    except subprocess.TimeoutExpired:
        result.blockers.append("pytest timed out (>5 minutes)")
    except FileNotFoundError:
        result.blockers.append("pytest not available")


def save_report(
    result: GateResult, output_path: str = "dist/build_readiness_report.json"
) -> None:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": result.status(),
        "exit_code": result.exit_code(),
        "blockers": result.blockers,
        "warnings": result.warnings,
        "blocker_count": len(result.blockers),
        "warning_count": len(result.warnings),
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# =========================
# Main
# =========================
def main() -> int:
    print("╔══════════════════════════════════════════════╗")
    print("║   🛡️ Guardian Build Readiness Gate v2.1      ║")
    print("║   Production Decision Gate                   ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    result = GateResult()

    print("🔍 Checking critical imports...")
    check_imports(result)

    print("🔍 Checking LedgerEvent integrity...")
    check_ledger_enum(result)

    print("🔍 Checking DTO invariants...")
    check_dto_invariants(result)

    print("🔍 Checking JSON messages (deep validation)...")
    check_json_messages(result)

    print("🔍 Running unit tests (max_failures=0)...")
    run_pytest(result, max_failures=0)

    save_report(result)

    print()
    print("═══════════ RESULT ═══════════")
    if result.blockers:
        print("❌ BUILD BLOCKED")
        for b in result.blockers:
            print(f"   🔴 {b}")
    elif result.warnings:
        print("⚠️ READY WITH WARNINGS")
        for w in result.warnings:
            print(f"   🟡 {w}")
    else:
        print("✅ BUILD READY")

    print()
    print(f"Status: {result.status()}")
    print(f"Exit Code: {result.exit_code()}")
    print("Report: dist/build_readiness_report.json")
    print("══════════════════════════════")

    return result.exit_code()


if __name__ == "__main__":
    sys.exit(main())
