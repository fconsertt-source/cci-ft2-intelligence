import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

def create_mock_data(path: str):
    """Creates a TSV with diverse v1.1.0 scenarios for visual testing.

    This writes a simple TSV without pandas so tests can run in minimal
    environments where pandas is not installed.
    """
    headers = [
        'center_id', 'center_name', 'decision', 'alert_level', 'vvm_stage',
        'stability_budget_consumed_pct', 'thaw_remaining_hours', 'category_display',
        'avg_temperature', 'min_temperature', 'max_temperature', 'num_ft2_entries',
        'decision_reasons'
    ]

    rows = [
        ['C001', 'Health Center A (Safe)', 'ACCEPTED', 'GREEN', 'NONE', '5.2', 'N/A', 'Fridge Vaccine', '4.5', '2.1', '6.8', '100', 'Safe'],
        ['C002', 'Warehouse Stage 3', 'ACCEPTED', 'YELLOW', 'STAGE_B', '100.0', 'N/A', 'Heat Sensitive', '7.2', '4.0', '9.5', '150', 'Warning: HER=82%'],
        ['C003', 'Mobile Unit Stage 4', 'REJECTED', 'RED', 'STAGE_D', '150.0', 'N/A', 'Highly Sensitive', '12.5', '5.5', '15.0', '200', 'Critical: HER=150%'],
        ['C004', 'Ultra Cold Hub', 'ACCEPTED', 'YELLOW', 'NONE', '65.0', '72.5', 'mRNA Vaccine', '3.8', '2.0', '5.2', '80', 'Warning: Stage 2'],
        ['C005', 'Critical Alert', 'REJECTED', 'RED', 'STAGE_D', '200.0', 'N/A', 'Heat Sensitive', '15.0', '10.0', '20.0', '50', 'Absolute Discard'],
    ]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\t'.join(headers) + '\n')
        for r in rows:
            fh.write('\t'.join(map(str, r)) + '\n')

    logger.info("Mock data created at: %s", path)

def main():
    output_dir = "data/output/visual_tests"
    os.makedirs(output_dir, exist_ok=True)
    
    data_path = os.path.join(output_dir, "mock_visual_data.tsv")
    create_mock_data(data_path)
    
    # Import heavy generator lazily
    try:
        from src.reporting.unified_pdf_generator import UnifiedPDFGenerator, ReportType
    except Exception as e:
        logger.error("Could not import UnifiedPDFGenerator: %s", e)
        return

    gen = UnifiedPDFGenerator(output_dir=output_dir)

    logger.info("Generating Official Visual Report...")
    official_path = gen.generate(ReportType.OFFICIAL, data_path, "visual_test_official.pdf")
    logger.info("Done: %s", official_path)

    logger.info("Generating Technical Visual Report...")
    tech_path = gen.generate(ReportType.TECHNICAL, data_path, "visual_test_tech.pdf")
    logger.info("Done: %s", tech_path)

    logger.info("Generating Arabic Visual Report...")
    arabic_path = gen.generate(ReportType.ARABIC, data_path, "visual_test_arabic.pdf")
    logger.info("Done: %s", arabic_path)

if __name__ == "__main__":
    main()
