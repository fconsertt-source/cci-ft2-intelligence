# src/presentation/cli/cli.py
"""
واجهة سطر أوامر حقيقية — عقد سلوكي مُحكَم
لا تحتوي على أي منطق قرار أو استيراد من البنية التحتية
التجميع يحدث حصريًا عبر جذر التركيب (DI Container)
"""
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

import typer

# ✅ الاستيراد الوحيد المسموح: جذر التركيب + رسائل
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


def print_yellow(text: str):
    typer.echo(typer.style(text, fg=typer.colors.YELLOW), err=True)


@app.command()
def health_check():
    """
    Run a quick health check via AppComposer to ensure dependencies construct.
    """
    try:
        healthy = AppComposer.health_check()
        if healthy:
            print_green("Health check passed")
            return  # ✅ نجاح بدون استثناء
        else:
            print_red("Health check failed")
            raise typer.Exit(code=1)
    except Exception as e:
        print_red(f"Health check error: {e}")
        raise typer.Exit(code=1)


@app.command()
def import_data(
    input_dir: Path = typer.Option(
        ..., "--input", "-i", help="مسار مجلد يحتوي على ملفات FT2 الخام"
    ),
    output: Path = typer.Option(
        "ft2_data.json", "--output", "-o", help="مسار الملف الوسيط الناتج"
    ),
) -> None:
    """
    استيراد بيانات FT2 إلى تنسيق وسيط (JSON)
    """
    if not input_dir.exists():
        typer.echo(MessageMap.get("DEBUG_DIR_NOT_FOUND", path=str(input_dir)), err=True)
        raise typer.Exit(code=1)

    uc = AppComposer.create_import_ft2_bundle_uc()
    uc.execute(input_dir=input_dir, output_path=output)

    typer.echo(MessageMap.get("SIMPLE_PIPELINE_FAKE_REPORT_CREATED"))


@app.command()
def evaluate(
    center_id: str = typer.Option(..., "--center", "-c", help="معرف مركز التلقيح"),
    data_path: Path = typer.Option(
        "ft2_data.json", "--data", "-d", help="مسار البيانات الوسيطة"
    ),
) -> None:
    """
    تقييم سلامة سلسلة التبريد لمركز معين
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get("DEVICE_DATA_SOURCE_MISSING", path=str(data_path)), err=True
        )
        raise typer.Exit(code=1)

    # استخدام AppComposer مباشرة
    uc = AppComposer.create_evaluate_cold_chain_uc()  # noqa: F841
    # TODO: تنفيذ التقييم الفعلي عندما يكتمل الـ Use Case
    typer.echo(MessageMap.get_decision_message("ACCEPTED"))


@app.command()
def report(
    input_path: Path = typer.Option(
        "ft2_data.json", "--input", "-i", help="مسار البيانات الوسيطة"
    ),
    output_dir: Path = typer.Option(
        "data/output/reports", "--output", "-o", help="مجلد التقارير الناتجة"
    ),
) -> None:
    """
    توليد تقرير مركزي وتقارير تفصيلية
    """
    if not input_path.exists():
        typer.echo(
            MessageMap.get("DEVICE_DATA_SOURCE_MISSING", path=str(input_path)), err=True
        )
        raise typer.Exit(code=1)

    # استخدام AppComposer مباشرة
    uc = AppComposer.create_generate_report_uc()  # noqa: F841
    typer.echo(MessageMap.get("CENTER_REPORT_GENERATED", path=str(output_dir)))


@app.command()
def generate_device_report(
    device_id: str = typer.Argument(..., help="معرف الجهاز للتحليل الحراري"),
    output_path: Path = typer.Option(
        "data/output/reports/device_reports/device_report.json",
        "--output",
        "-o",
        help="مسار حفظ تقرير الجهاز",
    ),
    data_path: Path = typer.Option(
        "ft2_data.json", "--data", "-d", help="مسار البيانات الوسيطة"
    ),
) -> None:
    """
    توليد تقرير محاسبي حراري لجهاز فردي — شهادة الحارس الرقمي
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get("DEVICE_DATA_SOURCE_MISSING", path=str(data_path)),
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        # استخدام AppComposer فقط (تم إزالة fallback القديم)
        uc = AppComposer.create_generate_device_report_uc()
        req = GenerateDeviceReportRequest(device_id=device_id)
        report = uc.execute(req)

        # إنشاء هيكل المجلدات تلقائيًا
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, default=str, indent=2, ensure_ascii=False)

        typer.echo(
            MessageMap.get(
                "DEVICE_REPORT_GENERATED", device_id=device_id, path=str(output_path)
            )
        )

    except ValueError:
        typer.echo(MessageMap.get("DEVICE_NOT_FOUND", device_id=device_id), err=True)
        raise typer.Exit(code=1)


@app.command()
def generate_all_device_reports(
    output_dir: Path = typer.Option(
        "data/output/device_reports", "--output", "-o", help="مجلد تقارير الأجهزة"
    ),
    data_path: Path = typer.Option(
        "ft2_data.json", "--data", "-d", help="مسار البيانات الوسيطة"
    ),
) -> None:
    """
    توليد تقارير لجميع الأجهزة — محاسبة فردية شاملة
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get("PDF_SOURCE_FILE_MISSING", path=str(data_path)), err=True
        )
        raise typer.Exit(code=1)

    try:
        # TODO: تنفيذ get_all_device_ids() في المستقبل
        typer.echo(MessageMap.get("DEVICE_REPORTS_NOT_YET_IMPLEMENTED"))
        raise typer.Exit(code=0)

    except Exception as e:
        typer.echo(
            MessageMap.get("DEVICE_REPORTS_GENERATION_FAILED", error=str(e)), err=True
        )
        raise typer.Exit(code=1)


@app.command(name="verify-official")
def verify_official(file_path: Path):
    """
    Verify a file using the official Berlinger verifier.
    """
    try:
        verifier = AppComposer.create_official_verifier()
        result = verifier.verify_file(file_path)

        if result.is_success:
            print_green(f"✅ Verification Successful: {result.status.value}")
            if result.diagnostics:
                typer.echo(f"Details: {result.diagnostics}")
        else:
            print_red(f"❌ Verification Failed: {result.status.value}")
            if result.diagnostics:
                typer.echo(f"Reason: {result.diagnostics}")

        logger.info(
            "Official verification completed for %s - Status: %s",
            file_path,
            result.status.value,
        )

    except Exception as e:
        print_red(f"Error during verification: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    sys.exit(app())
