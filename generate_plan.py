import os
import subprocess
import sys
from datetime import datetime

# محاولة استيراد المكتبة، وتثبيتها إذا لم تكن موجودة
try:
    from fpdf import FPDF, HTMLMixin
except ImportError:
    print("⚠️  مكتبة fpdf غير موجودة. جاري محاولة التثبيت...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf"])
        from fpdf import FPDF, HTMLMixin

        print("✅ تم تثبيت fpdf بنجاح.")
    except Exception:
        print("❌ فشل التثبيت التلقائي. يرجى تشغيل: pip install fpdf")
        sys.exit(1)


class PDFPlan(FPDF, HTMLMixin):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Digital Sentinel v2.0 - PDF Engine Upgrade Plan", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def chapter_title(self, num, title):
        self.set_font("Arial", "B", 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, f"{num}. {title}", 0, 1, "L", 1)
        self.ln(4)

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 8, title, 0, 1, "L")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 6, text)
        self.ln()

    def add_table(self, headers, data, col_widths):
        self.set_font("Arial", "B", 10)
        self.set_fill_color(230, 230, 230)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, "C", 1)
        self.ln()

        self.set_font("Arial", "", 9)
        for row in data:
            # استخدام multi_cell للسماح بتعدد الأسطر
            # لكن هذا يتطلب حساب الارتفاع الأقصى لكل صف
            max_height = 0
            for i, cell in enumerate(row):
                lines = self.multi_cell(
                    col_widths[i], 6, str(cell), border=0, split_only=True
                )
                max_height = max(max_height, len(lines) * 6)

            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_height, str(cell), 1, 0, "L")
            self.ln()


def generate_plan_pdf():
    pdf = PDFPlan()
    pdf.add_page()

    # === Main Title ===
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, "Executive Plan: PDF Engine Upgrade", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(
        0,
        8,
        f"Version: 2.0 - Production Hardening | Status: Approved for Implementation",
        0,
        1,
        "C",
    )
    pdf.ln(10)

    # === Section 1: Vision ===
    pdf.chapter_title("1", "Strategic Vision")
    pdf.body_text(
        "Migrate from the legacy, complex PDF generator to an enterprise-grade reporting engine that is clean, fully tested, forensically sound, and globally ready with full Arabic support."
    )

    # === Section 2: Current State ===
    pdf.chapter_title("2", "Current State Analysis")
    pdf.body_text(
        "The current engine (UnifiedPDFGenerator) is complex, hard to maintain, and causes test failures due to inconsistent interfaces and behavior. The existing wrapper is a temporary patch, not a solution."
    )

    # === Section 3: Action Plan ===
    pdf.chapter_title("3", "Action Plan (6-Week Roadmap)")

    # --- Phase 1 ---
    pdf.section_title("Phase 1: Evaluation & Refactoring (Weeks 1-2)")
    pdf.body_text(
        "Objective: Decompose the legacy engine into smaller, testable units."
    )
    headers = ["Task", "Action", "Target Files"]
    data = [
        (
            "Feature Inventory",
            "List all features of UnifiedPDFGenerator (reports, tables, charts).",
            "docs/pdf_engine_features.md",
        ),
        (
            "Create Builders",
            "Create separate classes for Header, Table, Chart, Footer.",
            "src/presentation/reporting/components/",
        ),
        (
            "Unify API",
            "Create a new engine with a unified `render(dto, report_type, language)` API.",
            "src/infrastructure/adapters/reporting/new_pdf_engine.py",
        ),
        (
            "Refactor Logic",
            "Move logic from the old engine to the new builders.",
            "src/presentation/reporting/components/",
        ),
    ]
    pdf.add_table(headers, data, [40, 80, 50])
    pdf.ln(5)

    # --- Phase 2 ---
    pdf.section_title("Phase 2: Arabic Support & Unit Testing (Weeks 3-4)")
    pdf.body_text(
        "Objective: Solve the Arabic text problem at its root and write comprehensive unit tests."
    )
    headers = ["Task", "Action", "Target Files"]
    data = [
        (
            "Integrate Arabic Processor",
            "Create an ArabicTextProcessor for reshape & bidi inside the new engine.",
            "components/arabic_processor.py",
        ),
        (
            "Add Unit Tests",
            "Write tests for each builder component (Header, Table, etc.).",
            "tests/unit/presentation/reporting/",
        ),
        (
            "Test Arabic Support",
            "Test the ArabicTextProcessor to ensure correct text shaping.",
            "tests/unit/.../test_arabic_processor.py",
        ),
        (
            "Update Golden Tests",
            "Modify Golden Master tests to expect successful Arabic text rendering.",
            "tests/golden/test_pdf_golden_master.py",
        ),
    ]
    pdf.add_table(headers, data, [40, 80, 50])
    pdf.ln(5)

    # --- Phase 3 ---
    pdf.section_title("Phase 3: Strategy Migration & Integration (Week 5)")
    pdf.body_text("Objective: Make the entire system use the new engine.")
    headers = ["Task", "Action", "Target Files"]
    data = [
        (
            "Update PDF Strategies",
            "Modify strategies to call the new engine.",
            "pdf_strategy.py",
        ),
        (
            "Remove Wrapper",
            "Delete the UnifiedPDFGeneratorWrapper completely.",
            "unified_pdf_generator_wrapper.py",
        ),
        (
            "Update DI Container",
            "Modify the DI container to wire strategies to the new engine.",
            "di_container.py",
        ),
        (
            "Run Integration Tests",
            "Ensure all use cases work with the new engine.",
            "tests/integration/",
        ),
    ]
    pdf.add_table(headers, data, [40, 80, 50])
    pdf.ln(5)

    # --- Phase 4 ---
    pdf.section_title("Phase 4: Documentation & Deployment (Week 6)")
    pdf.body_text("Objective: Document the changes and prepare for deployment.")
    headers = ["Task", "Action", "Target Files"]
    data = [
        (
            "Update Docs",
            "Explain how to use the new engine and add new report types.",
            "docs/reporting_engine.md",
        ),
        (
            "Update Golden Baseline",
            "Ensure the script works with the new engine.",
            "capture_golden_baseline.py",
        ),
        (
            "Review Readiness Gate",
            "Ensure all readiness checks pass.",
            "build_readiness_gate.py",
        ),
        (
            "Build Production Bundle",
            "Run the build script and verify the executable.",
            "build_production_bundle_windows.ps1",
        ),
    ]
    pdf.add_table(headers, data, [40, 80, 50])
    pdf.ln(5)

    # === Final Structure ===
    pdf.chapter_title("4", "Final Target Architecture")
    structure_text = """
src/
  infrastructure/
    adapters/
      reporting/
        new_pdf_engine.py      # New Engine
        pdf_strategy.py        # Updated
  presentation/
    reporting/
      components/              # New Builders
        header_builder.py
        table_builder.py
        chart_builder.py
        arabic_processor.py
    """
    pdf.set_font("Courier", "", 10)
    pdf.multi_cell(0, 5, structure_text)

    # === Output PDF ===
    filename = "Digital_Sentinel_v2_PDF_Engine_Upgrade_Plan.pdf"
    pdf.output(filename)
    print(f"\n✅ PDF plan generated successfully: {filename}")
    print(f"   Full Path: {os.path.abspath(filename)}")


if __name__ == "__main__":
    generate_plan_pdf()
