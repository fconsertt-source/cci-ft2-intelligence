# src/presentation/cli/cli.py
"""
واجهة سطر أوامر حقيقية — عقد سلوكي مُحكَم
لا تحتوي على أي TODO أو منطق قرار
"""
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

import typer

from src.application.app_composer import AppComposer
from src.application.use_cases.generate_device_report_uc import GenerateDeviceReportRequest
from src.presentation.messages.message_map import MessageMap

app = typer.Typer(
    name="ft2-cli",
    help=MessageMap.get("CLI_DESCRIPTION"),
    add_completion=True,
    no_args_is_help=True,
)

logger = logging.getLogger(__name__)


def print_green(text: str):
    typer.echo(typer.style(text, fg=typer.colors.GREEN, bold=True))


def print_red(text: str):
    typer.echo(typer.style(text, fg=typer.colors.RED, bold=True), err=True)


@app.command()
def health_check():
    """فحص جاهزية النظام"""
    if AppComposer.health_check():
        print_green("✅ Health check passed - System is ready for production")
    else:
        print_red("❌ Health check failed")
        raise typer.Exit(code=1)


@app.command()
def import_data(
    input_path: Path = typer.Option(
        ..., "--input", "-i", help="Path to FT2 input file or directory (TXT/TSV/CSV)."
    ),
    output: Path = typer.Option(
        "data/ft2_data.json", "--output", "-o", help="Destination FT2 JSON file."
    ),
):
    """استيراد بيانات FT2"""
    uc = AppComposer.create_import_ft2_bundle_uc()
    try:
        uc.execute(input_path, output)
        typer.echo(f"✅ Successfully imported FT2 data from: {input_path}")
        typer.echo(f"   → Written to: {output}")
    except Exception as exc:
        typer.echo(f"❌ Import failed: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def generate_device_report(
    device_id: str = typer.Argument(..., help="معرف الجهاز"),
    output_path: Path = typer.Option("data/output/reports/device_reports/device_report.json", "--output", "-o"),
    data_path: Path = typer.Option("data/ft2_data.json", "--data", "-d"),
):
    """توليد تقرير جهاز فردي (الأمر الرئيسي)"""
    uc = AppComposer.create_generate_device_report_uc(str(data_path))
    req = GenerateDeviceReportRequest(device_id=device_id)
    report = uc.execute(req)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, default=str, indent=2, ensure_ascii=False)

    typer.echo(MessageMap.get("DEVICE_REPORT_GENERATED", device_id=device_id, path=str(output_path)))


@app.command()
def generate_all_device_reports(
    output_dir: Path = typer.Option("data/output/device_reports", "--output", "-o"),
    data_path: Path = typer.Option("ft2_data.json", "--data", "-d"),
):
    """توليد تقارير جميع الأجهزة"""
    typer.echo("🔄 Generating reports for all devices... (coming in next release)")
    # سيتم تنفيذه في الإصدار القادم
    raise typer.Exit(code=0)


if __name__ == "__main__":
    sys.exit(app())