"""
Application Composer - الحارس الرقمي
مركز تكوين التبعيات للتطبيق
"""

import logging
import os
from datetime import datetime, timezone

from src.application.security.license_validator import LicenseValidator
from src.application.use_cases.generate_device_report_uc import GenerateDeviceReportUseCase
from src.application.use_cases.generate_pdf_report_uc import GeneratePDFReportUseCase
from src.application.use_cases.import_ft2_data_uc import ImportFt2DataUseCase
from src.domain.policies.trial_policy import TrialPolicy
from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import ThermalDegradationEstimator
from src.infrastructure.adapters.berlinger_ft2_reader import BerlingerFt2Reader
from src.infrastructure.adapters.json_ft2_data_writer import JsonFt2DataWriter
from src.infrastructure.adapters.json_vaccine_spec_repository import JsonVaccineSpecRepository
from src.infrastructure.adapters.validation_protocol_service import ValidationProtocolService
from src.infrastructure.repositories.device_repository import DeviceDataRepository
from src.infrastructure.security.encrypted_license_repository import EncryptedLicenseRepository
from src.infrastructure.security.fingerprint_provider import SystemFingerprintProvider
from src.infrastructure.security.license_guard import LicenseGuard

logger = logging.getLogger(__name__)


class AppComposer:
    """مصنع لبناء حالات الاستخدام مع التبعيات المطلوبة."""

    @staticmethod
    def _create_license_guard():
        env = os.getenv("CCI_ENV", "development").lower()
        public_key_path = os.path.expanduser("~/.cci_ft2/public.pem")
        license_path = os.path.expanduser("~/.cci_ft2/license.dat")

        os.makedirs(os.path.dirname(public_key_path), exist_ok=True)

        if env in ("development", "test"):
            # إنشاء ملفات وهمية آمنة للتطوير فقط
            if not os.path.exists(public_key_path):
                with open(public_key_path, "w") as f:
                    f.write("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtestkeyfordevonly\n-----END PUBLIC KEY-----\n")
            if not os.path.exists(license_path):
                with open(license_path, "w") as f:
                    f.write("DEV-TEST-LICENSE-2026")

        # تحميل المفتاح
        with open(public_key_path, "rb") as f:
            public_key_pem = f.read()

        fingerprint_provider = SystemFingerprintProvider()
        install_timestamp = fingerprint_provider.get_install_timestamp()

        try:
            install_datetime = datetime.fromisoformat(install_timestamp.replace("Z", "+00:00"))
        except Exception:
            install_datetime = datetime.now(timezone.utc)

        repo = EncryptedLicenseRepository(
            license_path=license_path,
            fingerprint=fingerprint_provider.get_machine_id(),
        )

        validator = LicenseValidator()
        policy = TrialPolicy(
            installation_time=install_datetime,
            trial_duration_days=90,
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
    def create_generate_device_report_uc(
        data_path: str | None = None,
    ) -> GenerateDeviceReportUseCase:
        logger.info("Building GenerateDeviceReportUseCase...")
        repository = DeviceDataRepository(json_path=data_path) if data_path else DeviceDataRepository()
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
    def create_import_ft2_bundle_uc() -> ImportFt2DataUseCase:
        logger.info("Building ImportFT2BundleUseCase (ImportFt2DataUseCase alias)...")
        reader = BerlingerFt2Reader()
        writer = JsonFt2DataWriter()
        uc = ImportFt2DataUseCase(reader=reader, writer=writer)
        logger.info("ImportFT2BundleUseCase built successfully")
        return uc

    @staticmethod
    def create_import_ft2_data_uc() -> ImportFt2DataUseCase:
        logger.info("Building ImportFt2DataUseCase...")
        reader = BerlingerFt2Reader()
        writer = JsonFt2DataWriter()
        uc = ImportFt2DataUseCase(reader=reader, writer=writer)
        logger.info("ImportFt2DataUseCase built successfully")
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
        except Exception as e:
            logger.error("❌ Health check failed: %s", e)
            return False