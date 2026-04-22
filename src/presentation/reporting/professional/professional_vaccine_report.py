from datetime import datetime
from pathlib import Path
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from .chart_generator import ReportChartGenerator
from src.shared.language_manager import lang


class ProfessionalVaccineReport:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.template_dir = self.base_dir / "templates"
        self.static_dir = self.base_dir / "static"
        self.fonts_dir = self.base_dir.parents[2] / "shared" / "fonts"
        self.locales_dir = self.base_dir.parents[2] / "shared" / "locales"

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.chart_gen = ReportChartGenerator()

    def _normalize_status(self, decision: str) -> str:
        normalized = str(decision or "").upper()
        if normalized in {"SAFE", "ACCEPTED", "PASS"}:
            return "safe"
        if normalized in {"PARTIAL", "WARNING", "USE_FIRST", "YELLOW"}:
            return "warning"
        if normalized in {"REJECTED", "DISCARD", "FAIL", "NO_DATA", "FAILED"}:
            return "discard"
        return "unknown"

    def _vvm_stage_label(self, stage: str) -> str:
        value = str(stage or "").upper().replace(" ", "_")
        if value.startswith("STAGE_"):
            return lang.get(f"vvm.{value.lower()}")
        return value or "-"

    def _load_language(self, language: str) -> None:
        try:
            lang.load_language(language, translations_dir=self.locales_dir)
        except FileNotFoundError:
            lang.load_language("en", translations_dir=self.locales_dir)

    def _translate(self, key: str, default: str) -> str:
        translated = lang.get(key)
        return default if translated == key else translated

    def _prepare_labels(self) -> dict:
        return {
            "report_municipality": self._translate("report.municipality", "Municipality"),
            "report_device_id": self._translate("report.device_id", "Device ID"),
            "report_officer_signature": self._translate("report.officer_signature", "Cold Chain Officer Signature"),
            "report_supervisor_signature": self._translate("report.supervisor_signature", "Municipality Vaccination Supervisor"),
            "report_center_name": self._translate("field.facility_name", "Facility Name"),
            "report_equipment_type": self._translate("field.unit_type", "Unit Type"),
            "report_vaccine_type": self._translate("vaccine.name", "Vaccine Name"),
            "report_temperature_range": self._translate("report.temperature_range", "Temperature Range: 2°C - 8°C"),
            "report_exposure_minutes": self._translate("report.exposure_minutes", "Exposure Minutes"),
            "report_id_label": self._translate("report.report_id", "Report ID"),
            "report_vvm": self._translate("report.vvm_distribution", "Virtual VVM"),
            "report_status_alert": self._translate("report.status_alert", "Status Alert"),
            "report_stability_budget": self._translate("report.stability_budget", "Stability Budget"),
            "report_category": self._translate("report.category", "Category"),
            "report_batch_analysis": self._translate("report.batch_analysis", "Detailed Batch Analysis"),
            "report_visual_trends": self._translate("report.visual_trends", "Visual Trends"),
            "chart_temperature_timeline": self._translate("chart.temp_title", "Temperature Timeline"),
            "chart_stability_budget": self._translate("report.stability_budget", "Stability Budget"),
            "no_chart_available": self._translate("msg.no_data", "Chart unavailable"),
            "footer_text": f"{self._translate('report.confidential', 'Confidential & Official')} · {self._translate('msg.copyright', 'All Rights Reserved © 2026')}"
        }

    def _build_render_context(self, context: dict, readings=None) -> dict:
        data = dict(context or {})
        language = data.get("language", "ar")
        self._load_language(language)
        is_rtl = lang.is_rtl
        dir_attr = "rtl" if is_rtl else "ltr"
        text_align = "right" if is_rtl else "left"

        report_id = data.get("report_id") or f"CCI-{uuid4().hex[:10].upper()}"
        generated_at = data.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        decision = data.get("decision", "UNKNOWN")
        judgment_class = self._normalize_status(decision)
        status_text = lang.get(f"status.{judgment_class}") if judgment_class in {"safe", "warning", "discard"} else lang.get("status.unknown")
        vvm_stage_label = self._vvm_stage_label(data.get("vvm_stage"))
        vvm_icon_class = {
            "safe": "vvm-stage-1",
            "warning": "vvm-stage-2",
            "discard": "vvm-stage-4",
        }.get(judgment_class, "vvm-stage-3")

        summary = {
            "total": int(data.get("summary", {}).get("total", 1) or 1),
            "safe": int(data.get("summary", {}).get("safe", 1 if judgment_class == "safe" else 0)),
            "warning": int(data.get("summary", {}).get("warning", 1 if judgment_class == "warning" else 0)),
            "discard": int(data.get("summary", {}).get("discard", 1 if judgment_class == "discard" else 0)),
        }

        timeline_path = None
        if readings:
            timeline_path = self.chart_gen.generate_temperature_timeline(readings)

        stability_path = self.chart_gen.generate_stability_budget_bar(
            float(data.get("stability_budget_consumed_pct", 0.0))
        )

        data.update(
            {
                "lang_code": language,
                "dir_attr": dir_attr,
                "text_align": text_align,
                "title": lang.get("report.official_title"),
                "subtitle": data.get("subtitle", lang.get("report.system_logic")),
                "generated_at_label": lang.get("report.generated_on"),
                "reference_label": lang.get("report.reference"),
                "report_id": report_id,
                "generated_at": generated_at,
                "judgment_class": judgment_class,
                "status_text": status_text,
                "vvm_stage_label": vvm_stage_label,
                "vvm_icon_class": vvm_icon_class,
                "summary": summary,
                "device_id": data.get("device_id", "-"),
                "center_name": data.get("center_name", "-"),
                "equipment_type": data.get("equipment_type", "-"),
                "vaccine_type": data.get("vaccine_type", "-"),
                "temp_min": data.get("temp_min", "-"),
                "temp_max": data.get("temp_max", "-"),
                "exposure_minutes": data.get("exposure_minutes", 0),
                "category_display": data.get("category_display", "-"),
                "stability_budget_consumed_pct": float(data.get("stability_budget_consumed_pct", 0.0)),
                "equipment_code": data.get("device_id", "N/A"),
                "supervisor_name": data.get("supervisor_name", "-"),
                "municipality": data.get("municipality", "-"),
                "temp_timeline_chart": timeline_path if timeline_path and timeline_path.startswith("data:") else Path(timeline_path).resolve().as_uri() if timeline_path else None,
                "stability_budget_chart": stability_path if stability_path and stability_path.startswith("data:") else Path(stability_path).resolve().as_uri() if stability_path else None,
                "font_tajawal_regular": str((self.fonts_dir / "Tajawal-Regular.ttf").resolve().as_uri()),
                "font_tajawal_bold": str((self.fonts_dir / "Tajawal-Bold.ttf").resolve().as_uri()),
            }
        )

        data["labels"] = self._prepare_labels()
        return data

    def render_vaccine_a4(self, context: dict, readings=None) -> bytes:
        render_context = self._build_render_context(context, readings=readings)

        template = self.env.get_template("vaccine_report_a4.html")
        html_content = template.render(**render_context)

        font_config = FontConfiguration()
        css = CSS(string="@page { size: A4; margin: 14mm; }", base_url=str(self.static_dir))

        return HTML(string=html_content, base_url=str(self.static_dir)).write_pdf(
            stylesheets=[css], font_config=font_config
        )

    def generate_vaccine_a4(self, context: dict, readings=None, filename: str = None):
        render_context = self._build_render_context(context, readings=readings)

        report_id = render_context.get("report_id") or f"CCI-{uuid4().hex[:10].upper()}"
        if not filename:
            filename = f"vaccine_report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        output_path = Path("data/output/reports") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pdf_bytes = self.render_vaccine_a4(render_context, readings=readings)
        output_path.write_bytes(pdf_bytes)

        print(f"✅ تم إنشاء تقرير اللقاح A4 بنجاح: {output_path.resolve()}")
        if render_context.get("temp_timeline_chart"):
            print(f"   📊 Timeline Chart: {Path(render_context['temp_timeline_chart']).name}")
        if render_context.get("stability_budget_chart"):
            print(f"   📊 Stability Budget Chart: {Path(render_context['stability_budget_chart']).name}")

        return str(output_path)
