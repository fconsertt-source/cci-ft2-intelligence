#!/usr/bin/env python3
"""
Capture golden baseline PDFs for all strategies.
✅ global declaration fixed
✅ جميع الحقول المتغيرة مُزالة قبل hash
"""
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure package root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration - ✅ تعريف في المستوى الأعلى
BASELINE_DIR = Path("tests/golden/baselines")
BASELINE_DIR.mkdir(parents=True, exist_ok=True)
# metadata file path is recalculated inside main() in case BASELINE_DIR is
# monkeypatched by tests or CLI.
METADATA_FILE = BASELINE_DIR / "golden_metadata.json"


def normalize_pdf_bytes(pdf_bytes: bytes) -> bytes:
    """Strip non-deterministic fields before hashing."""
    pdf_bytes = re.sub(
        rb"/CreationDate \(D:\d+\)", b"/CreationDate (Normalized)", pdf_bytes
    )
    pdf_bytes = re.sub(rb"/ModDate \(D:\d+\)", b"/ModDate (Normalized)", pdf_bytes)
    pdf_bytes = re.sub(rb"/Producer \([^)]+\)", b"/Producer (Normalized)", pdf_bytes)
    pdf_bytes = re.sub(rb"/ID \[[^]]+\]", b"/ID [(Normalized) (Normalized)]", pdf_bytes)
    return pdf_bytes


def calculate_hash(pdf_bytes: bytes) -> str:
    """Calculate SHA-256 hash after normalization."""
    normalized = normalize_pdf_bytes(pdf_bytes)
    return hashlib.sha256(normalized).hexdigest()


def create_test_dto():
    from src.application.dtos.device_report_dto import DeviceReportDTO
    return DeviceReportDTO.create_golden_baseline()



def main(languages: list[str] | None = None) -> bool:
    """Main entry point.

    ``languages`` - optional list of language codes to generate baselines for.
    If not provided, default to ``['ar']`` to match the existing behaviour.
    """
    try:
        from src.infrastructure.adapters.reporting.pdf_strategy import (
            ArabicPDFStrategy, OfficialPDFStrategy, TechnicalPDFStrategy)
    except ImportError as e:
        print(f"PDF strategies not available: {e}")
        return False

    strategies = {
        "official": OfficialPDFStrategy(),
        "technical": TechnicalPDFStrategy(),
        "arabic": ArabicPDFStrategy(),
    }

    metadata = {"reports": {}}
    dto = create_test_dto()

    # ensure metadata file path reflects current BASELINE_DIR
    global METADATA_FILE
    METADATA_FILE = BASELINE_DIR / "golden_metadata.json"
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)

    if languages is None:
        languages = ["ar"]

    print("=" * 60)
    print("📸 Capturing Golden Baseline for PDF Reports")
    print(f"Languages: {languages}")
    print("=" * 60)

    for lang in languages:
        # the DTO itself doesn't track language; pass via the strategy call
        for name, strat in strategies.items():
            key = f"{name}-{lang}"
            try:
                print(f"\n📄 Generating {key} report...")

                pdf_bytes = strat.generate(dto, language=lang)

                if not pdf_bytes.startswith(b"%PDF"):
                    raise ValueError("Invalid PDF signature")

                output_path = BASELINE_DIR / f"{key}.pdf"
                output_path.write_bytes(pdf_bytes)

                # compute a stable hash for later comparison
                from tests.golden.pdf_normalizer import calculate_golden_hash

                metadata["reports"][key] = {
                    "file": output_path.name,
                    "size": len(pdf_bytes),
                    "hash": calculate_golden_hash(pdf_bytes),
                }

                print(f"   ✅ Success ({len(pdf_bytes)} bytes)")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()

    METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"📊 Baseline metadata written to {METADATA_FILE}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Capture golden PDF baselines")
    parser.add_argument(
        "-l",
        "--languages",
        nargs="+",
        help="Language codes to include (e.g. ar en), defaults to ['ar']",
    )
    args = parser.parse_args()

    success = main(args.languages)
    sys.exit(0 if success else 1)
