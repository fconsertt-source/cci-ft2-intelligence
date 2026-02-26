from __future__ import annotations
from src.application.ports.i_reporter import IReporter


class GenerateReportUseCase:
    """Use Case for generating reports — depends ONLY on Ports."""
    
    def __init__(self, generator: IReporter):
        self._generator = generator

    def execute(self, input_path: str, output_path: str) -> str:
        # Phase 5 placeholder: real implementation will process input_path
        # For now, we prove the Port → Adapter chain works
        print(f"⚠️  Phase 5 placeholder: processing {input_path} → {output_path}")
        return output_path