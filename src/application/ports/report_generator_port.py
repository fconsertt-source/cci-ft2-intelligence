# src/application/ports/report_generator_port.py
from __future__ import annotations
from typing import Protocol

class ReportGeneratorPort(Protocol):
    """Port for generating reports — Application depends ONLY on this abstraction."""
    def generate(self, input_path: str, output_path: str) -> str:
        """Generate report and return absolute output path."""
        ...