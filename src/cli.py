"""Unified command‑line interface for the FT2 processing pipeline.

Implemented with **Typer** → type‑hints, auto‑completion, and easy testing.
Provides two high‑level commands:
* `import-ft2` – parses raw FT2 files into an intermediate JSON.
* `report`      – consumes that JSON and generates the unified PDF report.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from src.application.use_cases.import_ft2_data_uc import ImportFt2DataUseCase
from src.application.use_cases.generate_report_uc import GenerateReportUseCase
from src.infrastructure.logging import get_logger

# ---------------------------------------------------------
# Typer app definition
# ---------------------------------------------------------
app = typer.Typer(help="FT2 data processing and reporting tool")
logger = get_logger("ft2-cli")


# ---------------------------------------------------------
# Commands
# ---------------------------------------------------------
@app.command()
def import_ft2(
    input_dir: Path = typer.Option(
        ..., "--input-dir", "-i", help="Directory containing raw FT2 files"
    ),
    output_json: Path = typer.Option(
        "ft2_data.json",
        "--output-json",
        "-o",
        help="Path for the intermediate JSON representation",
    ),
) -> None:
    """Parse FT2 files and store a unified JSON representation."""
    uc = ImportFt2DataUseCase(...)
    uc.execute(input_dir=str(input_dir), output_path=str(output_json))
    typer.secho(f"✅ FT2 data written to {output_json}", fg=typer.colors.GREEN)


@app.command()
def report(
    ft2_json: Path = typer.Option(
        "ft2_data.json",
        "--ft2-json",
        "-f",
        help="Path to the FT2 JSON produced earlier",
    ),
    output_pdf: Path = typer.Option(
        "centers_report.pdf",
        "--output-pdf",
        "-p",
        help="Destination PDF report",
    ),
) -> None:
    """Generate the unified PDF report from the FT2 JSON."""
    uc = GenerateReportUC()
    uc.execute(input_path=str(ft2_json), output_path=str(output_pdf))
    typer.secho(f"📄 Report generated at {output_pdf}", fg=typer.colors.BLUE)


# ---------------------------------------------------------
# Entry‑point used by `poetry run ft2-cli` (or `python -m src.cli`)
# ---------------------------------------------------------
def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())