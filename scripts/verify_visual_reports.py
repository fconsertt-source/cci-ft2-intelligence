#!/usr/bin/env python3
"""
Visual Reports Verification Script
Generates test PDF reports and charts for QA/visual inspection.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# إضافة مسار src للمشروع الحالي
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from src.infrastructure.logging import get_logger
from src.infrastructure.pdf.unified_pdf_generator import UnifiedPDFGenerator, ReportType
from src.presentation.messages.message_map import MessageProvider

logger = get_logger(__name__)


def create_mock_data(output_path: str) -> None:
    """
    Create a mock TSV file for testing visual reports.
    """
    data = {
        "center_id": ["C001", "C002", "C003", "C004"],
        "center_name": [
            "Health Center A (Safe)",
            "Warehouse Stage 3",
            "Mobile Unit Stage 4",
            "Ultra Cold Hub",
        ],
        "category_display": ["General", "General", "General", "General"],
        "alert_level": ["GREEN", "RED", "RED", "YELLOW"],
        "stability_budget_consumed_pct": [12.5, 82.3, 95.0, 72.5],
        "thaw_remaining_hours": [None, None, None, None],
        "avg_temperature": [5.2, 9.1, 10.5, -2.3],
        "has_freeze": [False, False, False, True],
        "has_ccm_violation": [False, True, True, False],
        "decision_reasons": [
            "Normal",
            "Heat critical; discard",
            "Heat critical; discard",
            "Freeze violation",
        ],
    }
    df = pd.DataFrame(data)
    df.to_csv(output_path, sep="\t", index=False)
    logger.info("Mock data created at: %s", output_path)


def _create_placeholder_chart(path: Path) -> None:
    """
    Create a simple placeholder chart (PNG) using matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available, skipping chart generation")
        return

    plt.figure(figsize=(8, 4))
    plt.text(
        0.5,
        0.5,
        "Temperature Chart\n(Placeholder)",
        ha="center",
        va="center",
        fontsize=14,
    )
    plt.axis("off")
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def generate_visual_reports(
    output_dir: str = "data/output/visual_tests", language: str = "ar"
) -> None:
    """
    Generate all visual test reports and charts.
    This is the main function called by the script.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data_path = output_path / "mock_visual_data.tsv"
    create_mock_data(str(data_path))

    # ==================== Generate PDF Reports ====================
    try:
        # Use the real generator (now that dependencies are installed)
        gen = UnifiedPDFGenerator(language=language, output_dir=str(output_path))
    except Exception as e:
        logger.error("Could not initialize UnifiedPDFGenerator: %s", e)
        return

    def save_pdf(report_type: ReportType, filename: str) -> Optional[Path]:
        try:
            pdf_path = gen.generate(report_type, str(data_path), filename=filename)
            if pdf_path and isinstance(pdf_path, (str, Path)):
                pdf_path = Path(pdf_path)
                logger.info("Done: %s (size: %d bytes)", pdf_path, pdf_path.stat().st_size)
                return pdf_path
            else:
                logger.error("Unexpected return type from generate(): %s", type(pdf_path))
        except Exception as e:
            logger.error("Failed to generate %s: %s", filename, e)
        return None

    # Log the report header text safely (if generator has _process_text, use it)
    try:
        if hasattr(gen, "_process_text"):
            logger.info(gen._process_text(MessageProvider.get("VISUAL_REPORT_OFFICIAL")))
        else:
            logger.info(MessageProvider.get("VISUAL_REPORT_OFFICIAL"))
    except Exception:
        logger.info("Official Visual Report")

    save_pdf(ReportType.OFFICIAL, "visual_test_official.pdf")

    try:
        if hasattr(gen, "_process_text"):
            logger.info(gen._process_text(MessageProvider.get("VISUAL_REPORT_TECHNICAL")))
        else:
            logger.info(MessageProvider.get("VISUAL_REPORT_TECHNICAL"))
    except Exception:
        logger.info("Technical Visual Report")
    save_pdf(ReportType.TECHNICAL, "visual_test_tech.pdf")

    try:
        if hasattr(gen, "_process_text"):
            logger.info(gen._process_text(MessageProvider.get("VISUAL_REPORT_ARABIC")))
        else:
            logger.info(MessageProvider.get("VISUAL_REPORT_ARABIC"))
    except Exception:
        logger.info("Arabic Visual Report")
    save_pdf(ReportType.ARABIC, "visual_test_arabic.pdf")

    # ==================== Generate Placeholder Chart ====================
    chart_path = output_path / "temp_dist.png"
    _create_placeholder_chart(chart_path)
    logger.info("Created placeholder chart: %s", chart_path)


def main() -> None:
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate visual test reports")
    parser.add_argument(
        "--language",
        "-l",
        default="ar",
        choices=["ar", "en"],
        help="Language for reports (default: ar)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/output/visual_tests",
        help="Output directory for reports (default: data/output/visual_tests)",
    )
    args = parser.parse_args()

    generate_visual_reports(output_dir=args.output, language=args.language)


if __name__ == "__main__":
    main()