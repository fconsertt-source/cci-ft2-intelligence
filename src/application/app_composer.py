"""
Application Composer - الحارس الرقمي
مركز تكوين التبعيات للتطبيق

Security Enhanced v2.2:
- Integrated security components
- Optional authorization (offline/online mode)
- Audit logging support
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase
from src.application.use_cases.generate_report_uc import GenerateReportUseCase
from src.application.use_cases.import_ft2_bundle_uc import \
    ImportFT2BundleUseCase
from src.domain.services.exposure_analysis_service import \
    ExposureAnalysisService
from src.domain.services.regulatory_decision_service import \
    RegulatoryDecisionService
from src.domain.services.thermal_degradation_estimator import \
    ThermalDegradationEstimator
from src.infrastructure.adapters.json_vaccine_spec_repository import \
    JsonVaccineSpecRepository
from src.infrastructure.adapters.pdf_report_generator import PdfReportGenerator
from src.infrastructure.adapters.validation_protocol_service import \
    ValidationProtocolService
from src.infrastructure.repositories.device_repository import \
    DeviceDataRepository

logger = logging.getLogger(__name__)


class AppComposer:
    """مصنع لبناء حالات الاستخدام مع التبعيات المطلوبة."""

    # helper stub for environments where a full license guard would be
    # overkill (tests, demos, GUI quick launch, etc.)
    class _NoOpLicenseGuard:
        def ensure_active(self):
            # intentionally does nothing - always considered active
            pass

    # helper stub for offline mode authorization
    class _NoOpAuthorizer:
        def authorize(self, action: str, context: dict) -> bool:
            # Offline mode: always authorize (online mode will use real authorizer)
            return True

        def get_user_permissions(self, user_id: str) -> list:
            return ["read_reports", "write_reports"]

    @staticmethod
    def create_generate_device_report_uc() -> GenerateDeviceReportUseCase:
        """يبني حالة استخدام إنشاء تقرير الجهاز مع التبعيات الضرورية."""
        logger.info("Building GenerateDeviceReportUseCase...")
        repository = DeviceDataRepository()
        logger.info("Repository initialized: %s", type(repository).__name__)

        vaccine_specs = JsonVaccineSpecRepository()
        logger.info(
            "Vaccine Spec Repository initialized: %s", type(vaccine_specs).__name__
        )

        regulatory_service = RegulatoryDecisionService()
        logger.info(
            "Regulatory Service initialized: %s", type(regulatory_service).__name__
        )

        estimator = ThermalDegradationEstimator()
        logger.info("Estimator initialized: %s", type(estimator).__name__)

        # ✅ إضافة ExposureAnalysisService
        exposure_analysis = ExposureAnalysisService()
        logger.info(
            "Exposure Analysis Service initialized: %s",
            type(exposure_analysis).__name__,
        )

        validator = ValidationProtocolService()
        logger.info("Validator initialized: %s", type(validator).__name__)

        # a simple guard that will always succeed; enables use cases without
        # requiring the full license stack. production could swap in a real
        # LicenseGuard if needed by adjusting the composer accordingly.
        license_guard = AppComposer._NoOpLicenseGuard()
        logger.info("LicenseGuard initialized: %s", type(license_guard).__name__)

        uc = GenerateDeviceReportUseCase(
            device_repository=repository,
            vaccine_specifications=vaccine_specs,
            regulatory_decision_service=regulatory_service,
            estimator=estimator,
            exposure_analysis=exposure_analysis,
            validator=validator,
            license_guard=license_guard,
        )

        logger.info("UseCase built successfully")
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
    def create_generate_report_uc(
        authorizer: Optional[Any] = None, output_dir: Optional[str] = None
    ) -> GenerateReportUseCase:
        """
        Build secure report generation use case.

        Args:
            authorizer: Authorization service (uses NoOp for offline mode)
            output_dir: Directory for report output

        Returns:
            GenerateReportUseCase: Configured use case instance

        Security:
        - Integrates authorization (optional for offline)
        - Includes audit logging
        - Secure path handling
        """
        logger.info("Building GenerateReportUseCase...")

        # Create PDF generator
        output_dir = output_dir or os.getenv("CCIF_REPORT_OUTPUT_DIR", "reports")
        generator = PdfReportGenerator(output_dir=output_dir)
        logger.info("PdfReportGenerator initialized: %s", type(generator).__name__)

        # Create authorizer (NoOp for offline, real for online)
        if authorizer is None:
            env = os.getenv("CCIF_ENVIRONMENT", "development")
            if env == "production":
                # In production, try to import real authorizer
                try:
                    from src.application.security.local_authorizer import \
                        LocalAuthorizer

                    authorizer = LocalAuthorizer()
                    logger.info("LocalAuthorizer initialized for production")
                except ImportError:
                    authorizer = AppComposer._NoOpAuthorizer()
                    logger.warning(
                        "Using NoOpAuthorizer (LocalAuthorizer not available)"
                    )
            else:
                authorizer = AppComposer._NoOpAuthorizer()
                logger.info("NoOpAuthorizer initialized for development/offline")

        # Create audit logger
        from src.application.security.secure_logger import SecureAuditLogger

        log_file = os.getenv("CCIF_AUDIT_LOG_FILE", "logs/security_audit.log")
        audit_logger = SecureAuditLogger(log_file=log_file)
        logger.info("SecureAuditLogger initialized: %s", type(audit_logger).__name__)

        # Build use case
        uc = GenerateReportUseCase(
            generator=generator,
            authorizer=authorizer,
            audit_logger=audit_logger,
            output_dir=output_dir,
        )

        logger.info("GenerateReportUseCase built successfully")
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
            AppComposer.create_generate_report_uc()
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return False

    @staticmethod
    def create_evaluate_cold_chain_uc():
        """Use case create_evaluate_cold_chain_uc implemented in AppComposer"""
        logger.info("Building EvaluateColdChainSafetyUseCase for CLI...")

        license_guard = AppComposer._NoOpLicenseGuard()

        from src.application.use_cases.evaluate_cold_chain_safety_use_case import \
            EvaluateColdChainSafetyUseCase
        from src.domain.services.regulatory_decision_service import \
            RegulatoryDecisionService
        from src.domain.services.thermal_degradation_estimator import \
            ThermalDegradationEstimator
        from src.infrastructure.adapters.json_device_repository import \
            JsonDeviceRepository
        from src.infrastructure.adapters.json_vaccine_spec_repository import \
            JsonVaccineSpecRepository
        from src.infrastructure.adapters.validation_protocol_service import \
            ValidationProtocolService

        uc = EvaluateColdChainSafetyUseCase(
            device_repository=JsonDeviceRepository(),
            vaccine_specifications=JsonVaccineSpecRepository(),
            regulatory_decision_service=RegulatoryDecisionService(),
            estimator=ThermalDegradationEstimator(),
            validator=ValidationProtocolService(),
            license_guard=license_guard,
        )

        logger.info("EvaluateColdChainSafetyUseCase built successfully")
        return uc
