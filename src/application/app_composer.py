"""
Application Composer - الحارس الرقمي
مركز تكوين التبعيات للتطبيق
"""

import logging
import os
from datetime import datetime, timezone

from src.application.security.license_validator import LicenseValidator
from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase
from src.application.use_cases.generate_pdf_report_uc import \
    GeneratePDFReportUseCase
from src.application.use_cases.import_ft2_bundle_uc import \
    ImportFT2BundleUseCase
from src.domain.policies.trial_policy import TrialPolicy
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator
from src.infrastructure.adapters.json_vaccine_spec_repository import \
    JsonVaccineSpecRepository
from src.infrastructure.adapters.validation_protocol_service import \
    ValidationProtocolService
from src.infrastructure.repositories.device_repository import \
    DeviceDataRepository
from src.infrastructure.security.encrypted_license_repository import \
    EncryptedLicenseRepository
from src.infrastructure.security.fingerprint_provider import \
    SystemFingerprintProvider
from src.infrastructure.security.license_guard import \
    LicenseGuard

logger = logging.getLogger(__name__)


class AppComposer:
    """مصنع لبناء حالات الاستخدام مع التبعيات المطلوبة."""

    # helper stub for environments where a full license guard would be
    # overkill (tests, demos, GUI quick launch, etc.)
    class _NoOpLicenseGuard:
        def ensure_active(self):
            env = os.getenv("CCI_ENV", "development").lower()
            if env == "production":
                raise RuntimeError(
                    "NoOpLicenseGuard is unsafe in production. Configure a real LicenseGuard."
                )

    @staticmethod
    def _create_license_guard():
        env = os.getenv("CCI_ENV", "development").lower()
        if env != "production":
            return AppComposer._NoOpLicenseGuard()

        public_key_path = os.path.expanduser("~/.cci_ft2/public.pem")
        license_path = os.path.expanduser("~/.cci_ft2/license.dat")

        if not os.path.exists(public_key_path):
            raise FileNotFoundError(
                f"License public key not found at {public_key_path}. "
                "Production requires a valid license guard."
            )

        if not os.path.exists(license_path):
            raise FileNotFoundError(
                f"Encrypted license file not found at {license_path}. "
                "Production requires a valid license guard."
            )

        with open(public_key_path, "rb") as f:
            public_key_pem = f.read()

        fingerprint_provider = SystemFingerprintProvider()
        install_timestamp = fingerprint_provider.get_install_timestamp()
        try:
            install_datetime = datetime.fromisoformat(
                install_timestamp.replace("Z", "+00:00")
            )
        except Exception:
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

        return LicenseGuard(
            license_repo=repo,
            validator=validator,
            policy=policy,
            fingerprint_provider=fingerprint_provider,
            public_key_pem=public_key_pem,
        )

    @staticmethod
    def create_generate_device_report_uc() -> GenerateDeviceReportUseCase:
        """يبني حالة استخدام إنشاء تقرير الجهاز مع التبعيات الضرورية."""
        logger.info("Building GenerateDeviceReportUseCase...")
        repository = DeviceDataRepository()
        logger.info("Repository initialized: %s", type(repository).__name__)

        vaccine_specs = JsonVaccineSpecRepository()
        logger.info(
            f"Vaccine Spec Repository initialized: {type(vaccine_specs).__name__}"
        )

        regulatory_service = RegulatoryDecisionService()
        logger.info(
            f"Regulatory Service initialized: {type(regulatory_service).__name__}"
        )

        estimator = ThermalDegradationEstimator()
        logger.info("Estimator initialized: %s", type(estimator).__name__)

        validator = ValidationProtocolService()
        logger.info("Validator initialized: %s", type(validator).__name__)

        license_guard = AppComposer._create_license_guard()
        logger.info("LicenseGuard initialized: %s", type(license_guard).__name__)

        # ملاحظة: سيتم إضافة التبعيات الأخرى (مثل مولد PDF) هنا تدريجياً
        # حسب الخطة الموضوعة.
        uc = GenerateDeviceReportUseCase(
            device_repository=repository,
            vaccine_specifications=vaccine_specs,
            regulatory_decision_service=regulatory_service,
            estimator=estimator,
            validator=validator,
            license_guard=license_guard,
        )

        logger.info("UseCase built successfully")
        return uc

    @staticmethod
    def create_generate_pdf_report_uc() -> GeneratePDFReportUseCase:
        """يبني حالة استخدام إنشاء تقرير PDF مع التبعيات الضرورية."""
        logger.info("Building GeneratePDFReportUseCase...")
        from src.infrastructure.adapters.reporting.new_pdf_engine import PDFGenerator

        pdf_generator = PDFGenerator()
        logger.info("PDF Generator initialized: %s", type(pdf_generator).__name__)

        uc = GeneratePDFReportUseCase(pdf_generator=pdf_generator)
        logger.info("PDF UseCase built successfully")
        return uc

    @staticmethod
    def create_import_ft2_bundle_uc() -> ImportFT2BundleUseCase:
        logger.info("Building ImportFT2BundleUseCase...")
        repository = DeviceDataRepository()
        ledger_writer = None  # to be injected by caller if needed
        uc = ImportFT2BundleUseCase(repository=repository, ledger_writer=ledger_writer)
        logger.info("UseCase built successfully")
        return uc

    @staticmethod
    def health_check() -> bool:
        """
        فحص صحي سريع للتأكد من أن التبعيات قابلة للإنشاء.

        Returns:
            True إذا كان النظام جاهزاً، False otherwise
        """
        try:
            AppComposer.create_generate_device_report_uc()
            AppComposer.create_import_ft2_bundle_uc()
            AppComposer.create_generate_pdf_report_uc()
            logger.info("Health check passed")
            return True
        except Exception as e:
                logger.error("Health check failed: %s", e)
                return False
