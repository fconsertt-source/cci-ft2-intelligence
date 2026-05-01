import logging
import os
from datetime import datetime, timezone

# src/composition_root/app_composer.py
from .di_container import DIContainer
from src.application.security.license_validator import LicenseValidator
from src.application.services.judgment_engine import JudgmentEngine
from src.application.ports.i_license_guard import ILicenseGuard
from src.application.use_cases.generate_device_report_uc import GenerateDeviceReportUseCase
from src.application.use_cases.generate_pdf_report_uc import GeneratePDFReportUseCase
from src.application.use_cases.import_ft2_bundle_uc import ImportFT2BundleUseCase
from src.domain.exceptions import BaseSystemException
from src.domain.policies.trial_policy import TrialPolicy
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import ThermalDegradationEstimator


logger = logging.getLogger(__name__)


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


class AppComposer:
    """Factory for building use cases at the composition boundary."""

    @staticmethod
    def _create_license_guard():
        from src.infrastructure.security.encrypted_license_repository import (
            EncryptedLicenseRepository,
        )
        from src.infrastructure.security.fingerprint_provider import (
            SystemFingerprintProvider,
        )
        from src.infrastructure.security.license_guard import LicenseGuard

        env = os.getenv("CCI_ENV", "development").lower()
        public_key_path = os.path.expanduser("~/.cci_ft2/public.pem")
        license_path = os.path.expanduser("~/.cci_ft2/license.dat")

        os.makedirs(os.path.dirname(public_key_path), exist_ok=True)

        if env in ("development", "test"):
            if not os.path.exists(public_key_path):
                with open(public_key_path, "w") as f:
                    f.write("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtestkeyfordevonly\n-----END PUBLIC KEY-----\n")
            if not os.path.exists(license_path):
                with open(license_path, "w") as f:
                    f.write("DEV-TEST-LICENSE-2026")

        with open(public_key_path, "rb") as f:
            public_key_pem = f.read()

        fingerprint_provider = SystemFingerprintProvider()
        install_timestamp = fingerprint_provider.get_install_timestamp()

        try:
            install_datetime = datetime.fromisoformat(install_timestamp.replace("Z", "+00:00"))
        except ValueError:
            install_datetime = datetime.now(timezone.utc)

        repo = EncryptedLicenseRepository(
            license_path=license_path,
            fingerprint=fingerprint_provider.get_machine_id(),
        )

        validator = LicenseValidator()
        policy = TrialPolicy(
            installation_time=install_datetime,
            trial_duration_days=365,
        )

        guard = LicenseGuard(
            license_repo=repo,
            validator=validator,
            policy=policy,
            fingerprint_provider=fingerprint_provider,
            public_key_pem=public_key_pem,
        )

        logger.info("LicenseGuard initialized successfully (real guard)")
        return guard

    @staticmethod
    def create_generate_device_report_uc() -> GenerateDeviceReportUseCase:
        from src.infrastructure.adapters.json_vaccine_spec_repository import (
            JsonVaccineSpecRepository,
        )
        from src.infrastructure.adapters.validation_protocol_service import (
            ValidationProtocolService,
        )
        from src.infrastructure.repositories.device_repository import DeviceDataRepository
        from src.infrastructure.utils.config_loader import ConfigLoader

        logger.info("Building GenerateDeviceReportUseCase...")
        repository = DeviceDataRepository()
        vaccine_specs = JsonVaccineSpecRepository()
        regulatory_service = RegulatoryDecisionService()
        estimator = ThermalDegradationEstimator()
        validator = ValidationProtocolService()
        license_guard = AppComposer._create_license_guard()

        uc = GenerateDeviceReportUseCase(
            device_repository=repository,
            vaccine_specifications=vaccine_specs,
            regulatory_decision_service=regulatory_service,
            estimator=estimator,
            validator=validator,
            license_guard=license_guard,
            config_getter=ConfigLoader.get,
        )
        logger.info("GenerateDeviceReportUseCase built successfully")
        return uc

    @staticmethod
    def create_generate_pdf_report_uc() -> GeneratePDFReportUseCase:
        logger.info("Building GeneratePDFReportUseCase...")
        from src.infrastructure.adapters.reporting.new_pdf_engine import PDFGenerator

        pdf_generator = PDFGenerator()
        uc = GeneratePDFReportUseCase(pdf_generator=pdf_generator)
        logger.info("GeneratePDFReportUseCase built successfully")
        return uc

    @staticmethod
    def create_import_ft2_bundle_uc() -> ImportFT2BundleUseCase:
        from src.infrastructure.repositories.device_repository import DeviceDataRepository

        logger.info("Building ImportFT2BundleUseCase...")
        repository = DeviceDataRepository()
        uc = ImportFT2BundleUseCase(repository=repository, ledger_writer=None)
        logger.info("ImportFT2BundleUseCase built successfully")
        return uc

    @staticmethod
    def health_check() -> bool:
        """فحص صحي سريع قبل الإنتاج"""
        try:
            AppComposer.create_generate_device_report_uc()
            AppComposer.create_import_ft2_bundle_uc()
            AppComposer.create_generate_pdf_report_uc()
            logger.info("✅ Health check passed - System is production ready")
            return True
        except BaseSystemException as e:
            logger.error("❌ Health check failed with system exception: %s", e)
            return False
        except Exception as e:
            logger.error("❌ Health check failed due to unexpected error: %s", e)
            return False
