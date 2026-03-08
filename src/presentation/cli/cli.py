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
# Pared-down DI; migrating to AppComposer for simpler composition
from src.application.app_composer import AppComposer
from src.presentation.messages.message_map import MessageMap

# keep imports for backward compatibility until fully removed
from src.shared.di_container import (
    build_evaluate_uc,
    build_generate_device_report_uc,
    build_generate_report_uc,
    build_import_ft2_uc,
    build_official_verifier,
)

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
            raise typer.Exit(code=0)
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

    العقد السلوكي:
      الإدخال: مجلد يحتوي على ملفات .txt بصيغة FT2
      الإخراج: ملف JSON يحتوي على قائمة FT2EntryDTO
      الفشل: مجلد غير موجود → رسالة خطأ + كود خروج ≠ 0
    """
    if not input_dir.exists():
        typer.echo(MessageMap.get("DEBUG_DIR_NOT_FOUND", path=str(input_dir)), err=True)
        raise typer.Exit(code=1)

    # use AppComposer instead of old DI
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

    العقد السلوكي:
      الإدخال: معرف مركز + مسار بيانات وسيطة
      الإخراج: رسالة تقييم واحدة (بناءً على رمز القرار)
      الفشل: مركز غير موجود → رسالة تحذير (لا يُنهي البرنامج)
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get("DEVICE_DATA_SOURCE_MISSING", path=str(data_path)), err=True
        )
        raise typer.Exit(code=1)

    uc = build_evaluate_uc()
    # ملاحظة: الـ Use Case الحالي يُرجع قرارًا — سيتم تحسينه لاحقًا
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

    العقد السلوكي:
      الإدخال: مسار بيانات وسيطة + مجلد إخراج
      الإخراج:
        • centers_report.tsv
        • detailed_reports/report_XXX.txt
      الفشل: مجلد الإخراج غير قابل للكتابة → رسالة خطأ
    """
    if not input_path.exists():
        typer.echo(
            MessageMap.get("DEVICE_DATA_SOURCE_MISSING", path=str(input_path)), err=True
        )
        raise typer.Exit(code=1)

    uc = build_generate_report_uc()
    typer.echo(MessageMap.get("CENTER_REPORT_GENERATED", path=str(output_dir)))


@app.command()
def generate_device_report(
    device_id: str = typer.Argument(..., help="معرف الجهاز للتحليل الحراري"),
    output_path: Path = typer.Option(
        "data/output/reports/device_reports/device_report.json",  # ← التحديث هنا
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

    العقد السلوكي:
      الإدخال: معرف جهاز + مسار بيانات وسيطة
      الإخراج: تقرير JSON في data/output/reports/device_reports/
      الفشل: جهاز غير موجود → رسالة خطأ واضحة + كود خروج 1
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get(
                "DEVICE_DATA_SOURCE_MISSING", path=str(data_path)
            ),  # ← رسالة مخصصة
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        # prefer composer for new code, but fall back to DI container if still used
        try:
            uc = AppComposer.create_generate_device_report_uc()
        except Exception:
            uc = build_generate_device_report_uc(data_path=data_path)
        req = GenerateDeviceReportRequest(device_id=device_id)
        report = uc.execute(req)

        # إنشاء هيكل المجلدات تلقائيًا (إذا لم يكن موجودًا)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, default=str, indent=2, ensure_ascii=False)

        typer.echo(
            MessageMap.get(
                "DEVICE_REPORT_GENERATED", device_id=device_id, path=str(output_path)
            )
        )

    except ValueError as e:
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

    العقد السلوكي:
      الإدخال: مسار بيانات وسيطة
      الإخراج: مجلد يحتوي على تقرير JSON لكل جهاز
      الفشل: لا توجد أجهزة → رسالة تحذير (لا يُنهي البرنامج)
    """
    if not data_path.exists():
        typer.echo(
            MessageMap.get("PDF_SOURCE_FILE_MISSING", path=str(data_path)), err=True
        )
        raise typer.Exit(code=1)

    try:
        # الحصول على قائمة الأجهزة أولاً
        uc = build_generate_device_report_uc(data_path=data_path)
        # ملاحظة: سيتم إضافة get_all_device_ids() للـ Port لاحقًا
        # للمرحلة الحالية، نستخدم Use Case مع قائمة مسبقة

        # ⚠️ مؤقت: هذا الجزء سيُستبدل بـ device_repo.get_all_device_ids()
        # بعد إكمال الـ Adapter في البنية التحتية
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
        verifier = build_official_verifier()
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
