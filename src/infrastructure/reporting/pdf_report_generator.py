# src/infrastructure/reporting/pdf_report_generator.py
"""
PDF Report Generator for Device and Center Reports.
Implements IReportGenerator port using matplotlib + reportlab.
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from dataclasses import asdict, is_dataclass
from src.application.ports.i_report_generator import IReportGenerator
from src.application.dtos.center_report_dto import CenterReportDTO
from src.application.dtos.device_report_dto import DeviceReportDTO
from src.infrastructure.reporting.formatters.date_formatter import DateFormatter
from src.infrastructure.reporting.formatters.number_formatter import NumberFormatter
from src.infrastructure.utils.config_loader import ConfigLoader


class PDFReportGenerator(IReportGenerator):
    """PDF report generator using matplotlib for charts and reportlab for PDF."""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or "data/output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = ConfigLoader()

    def generate_device_report(self, data: Any, language: str) -> Dict[str, Any]:
        """Generate device report PDF."""
        if is_dataclass(data):
            data = asdict(data)

        if not isinstance(data, dict):
            raise TypeError("data must be a dict or DeviceReportDTO instance")

        # Validate required fields are present
        required_fields = [
            "device_id",
            "center_name",
            "decision",
            "vvm_stage",
            "stability_budget_consumed_pct",
            "decision_reasons",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        filename = f"device_{data['device_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename

        # Generate PDF content
        self._create_device_pdf(data, filepath, language)

        # Calculate hash for integrity
        import hashlib
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return {
            "file_path": str(filepath),
            "hash": file_hash,
            "filename": filename,
            "generated_at": datetime.now().isoformat()
        }

    def generate_center_report(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Generate center report PDF."""
        dto = CenterReportDTO(**data)
        filename = f"center_{dto.center_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename

        # Generate PDF content
        self._create_center_pdf(dto, filepath, language)

        # Calculate hash
        import hashlib
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return {
            "file_path": str(filepath),
            "hash": file_hash,
            "filename": filename,
            "generated_at": datetime.now().isoformat()
        }

    def _create_device_pdf(self, data: Dict[str, Any], filepath: Path, language: str):
        """Create device report PDF."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title = f"Device Report - {data['device_id']}" if language == 'en' else f"تقرير الجهاز - {data['device_id']}"
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))

            # Basic info
            stability_pct = NumberFormatter.format_percentage(data['stability_budget_consumed_pct'])
            info_data = [
                ["Center", data['center_name']],
                ["Decision", data['decision']],
                ["VVM Stage", data['vvm_stage']],
                ["Stability Budget", stability_pct],
            ]
            table = Table(info_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))

            # Decision reasons
            if data.get('decision_reasons'):
                reasons_title = "Decision Reasons" if language == 'en' else "أسباب القرار"
                story.append(Paragraph(reasons_title, styles['Heading2']))
                for reason in data['decision_reasons']:
                    story.append(Paragraph(f"• {reason}", styles['Normal']))
                story.append(Spacer(1, 12))

            doc.build(story)

        except ImportError:
            # Fallback to simple text file if reportlab not available
            with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Device Report - {data['device_id']}\n")
                f.write(f"Center: {data['center_name']}\n")
                f.write(f"Decision: {data['decision']}\n")
                f.write(f"VVM Stage: {data['vvm_stage']}\n")

    def _create_center_pdf(self, dto: CenterReportDTO, filepath: Path, language: str):
        """Create center report PDF."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title = f"Center Report - {dto.center_name}" if language == 'en' else f"تقرير المركز - {dto.center_name}"
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))

            # Summary
            summary_data = [
                ["Total Devices", str(dto.total_devices)],
                ["Safe Devices", str(dto.safe_devices)],
                ["Rejected Devices", str(dto.rejected_devices)],
                ["Partial Devices", str(dto.partial_devices)]
            ]
            table = Table(summary_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)

            doc.build(story)

        except ImportError:
            # Fallback
            with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Center Report - {dto.center_name}\n")
                f.write(f"Total Devices: {dto.total_devices}\n")
                f.write(f"Safe: {dto.safe_devices}, Rejected: {dto.rejected_devices}, Partial: {dto.partial_devices}\n")