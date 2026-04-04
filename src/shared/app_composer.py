# src/composition_root/app_composer.py
from .di_container import DIContainer
from src.application.services.judgment_engine import JudgmentEngine
from src.application.ports.i_license_guard import ILicenseGuard


def compose_phase1(container: DIContainer):
    """Register Phase 1 dependencies."""
    # Judgment engine (pure application service)
    container.register_instance(JudgmentEngine, JudgmentEngine())


def compose_phase2_reports(container: DIContainer):
    """Register Phase 2 reporting dependencies."""
    try:
        from src.application.ports.i_report_generator import IReportGenerator
        from src.application.ports.i_ledger_service import ILedgerService
        from src.application.ports.performance_monitor_port import PerformanceMonitorPort
        from src.infrastructure.reporting.pdf_report_generator import PDFReportGenerator
        from src.infrastructure.ledger.ledger_service import LedgerService
        from src.infrastructure.performance.performance_monitor import PerformanceMonitor

        container.register_instance(IReportGenerator, PDFReportGenerator())
        container.register_instance(ILedgerService, LedgerService())
        container.register_instance(PerformanceMonitorPort, PerformanceMonitor())
        print("✅ Phase 2 reporting dependencies registered")
    except ImportError as exc:
        print(f"⚠️ Phase 2 reporting dependencies not available yet: {exc}")


def compose_application(container: DIContainer):
    """Main composition entrypoint."""
    compose_phase1(container)
    # compose_phase2_reports(container)  # Uncomment when reports module is ready
