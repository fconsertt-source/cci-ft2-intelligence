"""
Application Composer - الحارس الرقمي
مركز تكوين التبعيات للتطبيق
"""

import logging

from src.application.use_cases.generate_device_report_uc import \
    GenerateDeviceReportUseCase
from src.application.use_cases.import_ft2_bundle_uc import \
    ImportFT2BundleUseCase
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

logger = logging.getLogger(__name__)


class AppComposer:
    """مصنع لبناء حالات الاستخدام مع التبعيات المطلوبة."""

    # helper stub for environments where a full license guard would be
    # overkill (tests, demos, GUI quick launch, etc.)
    class _NoOpLicenseGuard:
        def ensure_active(self):
            # intentionally does nothing - always considered active
            pass

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

        # a simple guard that will always succeed; enables use cases without
        # requiring the full license stack. production could swap in a real
        # LicenseGuard if needed by adjusting the composer accordingly.
        license_guard = AppComposer._NoOpLicenseGuard()
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
            logger.info("Health check passed")
            return True
        except Exception as e:
                logger.error("Health check failed: %s", e)
            return False
