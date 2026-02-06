# src/shared/di_container.py
"""Simple Composition Root / DI helpers.
Centralizes construction so Presentation and Application do not `new` domain components.
"""

from src.application.use_cases.evaluate_cold_chain_safety_use_case import EvaluateColdChainSafetyUseCase
from src.application.use_cases.import_ft2_data_uc import ImportFt2DataUseCase
from src.application.use_cases.generate_report_uc import GenerateReportUseCase
from src.infrastructure.adapters.default_ft2_reader import DefaultFt2Reader
from src.infrastructure.adapters.json_ft2_data_writer import JsonFt2DataWriter


def build_import_ft2_uc() -> ImportFt2DataUseCase:
    """Builds the Import FT2 Data Use Case with its dependencies."""
    reader = DefaultFt2Reader()
    writer = JsonFt2DataWriter()
    return ImportFt2DataUseCase(reader=reader, writer=writer)


def build_evaluate_uc() -> EvaluateColdChainSafetyUseCase:
    """Explicit Composition Root wiring.
    Use Case is stateless - no infrastructure dependencies needed.
    """
    return EvaluateColdChainSafetyUseCase()


def build_generate_report_uc() -> GenerateReportUseCase:
    """Placeholder implementation for Phase 4 validation."""
    class MockGenerator:
        def generate(self, *args, **kwargs):
            return "reports/mock_report.txt"
    
    class MockValidator:
        def validate(self, *args, **kwargs):
            pass
    
    return GenerateReportUseCase(generator=MockGenerator(), validator=MockValidator())