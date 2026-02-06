# src/shared/di_container.py
"""Simple Composition Root / DI helpers.
Centralizes construction so Presentation and Application do not `new` domain components.
"""

from src.application.use_cases.evaluate_cold_chain_safety_use_case import EvaluateColdChainSafetyUseCase
from src.application.use_cases.import_ft2_data_uc import ImportFt2DataUseCase
from src.application.use_cases.generate_report_uc import GenerateReportUseCase
from src.application.ports.report_generator_port import ReportGeneratorPort
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


class MockReportGenerator:
    """Mock adapter implementing ReportGeneratorPort for Phase 4 validation.
    
    This proves that:
      - Ports enforce contractual boundaries
      - DI container is the ONLY place for adapter instantiation
      - Application layer never depends on concrete infrastructure
    """
    def generate(self, input_path: str, output_path: str) -> str:
        print("Mock-generating report...")
        return output_path


def build_generate_report_uc() -> GenerateReportUseCase:
    """Composition Root wiring for report generation.
    
    This is the ONLY place where infrastructure adapters (even mocks) are instantiated
    and wired to application-layer Use Cases via Ports.
    """
    generator: ReportGeneratorPort = MockReportGenerator()
    return GenerateReportUseCase(generator=generator)