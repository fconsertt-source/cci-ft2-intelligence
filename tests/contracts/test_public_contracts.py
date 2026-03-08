"""
اختبارات العقود العامة — تمنع كسر الواجهات دون قصد
"""

import inspect

import pytest


class TestPDFWrapperContract:
    """عقد UnifiedPDFGeneratorWrapper — لا يُسمح بتغييره"""

    def test_wrapper_class_exists(self):
        from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
            UnifiedPDFGeneratorWrapper,
        )

        assert UnifiedPDFGeneratorWrapper is not None

    def test_wrapper_has_generate_method(self):
        from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
            UnifiedPDFGeneratorWrapper,
        )

        assert hasattr(UnifiedPDFGeneratorWrapper, "generate")
        sig = inspect.signature(UnifiedPDFGeneratorWrapper.generate)
        assert "dto" in sig.parameters

    def test_factory_function_exists(self):
        from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
            get_pdf_generator,
        )

        assert callable(get_pdf_generator)


class TestUseCaseContract:
    """عقد GenerateDeviceReportUseCase — لا يُسمح بتغيير توقيع execute"""

    def test_execute_signature_accepts_request_dto(self):
        from src.application.use_cases.generate_device_report_uc import (
            GenerateDeviceReportUseCase,
        )
        from src.application.use_cases.requests import GenerateDeviceReportRequest

        sig = inspect.signature(GenerateDeviceReportUseCase.execute)
        params = list(sig.parameters.keys())

        # يجب أن يكون المعامل الثاني هو request من نوع GenerateDeviceReportRequest
        assert "request" in params
        # التحقق من النوع إن أمكن
        annotation = sig.parameters["request"].annotation
        # accept the class directly or any Optional wrapper; the exact
        # typing annotation may vary (e.g. Optional[], Union[], etc.).  We'll
        # just ensure the request type name appears in the repr.
        assert (
            annotation == GenerateDeviceReportRequest
            or "GenerateDeviceReportRequest" in str(annotation)
            or annotation == inspect.Parameter.empty
        )


class TestDomainEntityContract:
    """عقد VaccinationCenter — لا يُسمح بحذف الدوال العامة"""

    def test_vaccination_center_has_required_methods(self):
        from src.domain.entities.vaccination_center import VaccinationCenter

        required = ["add_ft2_entry", "decision", "_count_freeze_events"]
        for method in required:
            assert hasattr(VaccinationCenter, method), f"Missing: {method}"

    def test_decision_is_property_with_setter(self):
        from src.domain.entities.vaccination_center import VaccinationCenter

        assert isinstance(
            inspect.getattr_static(VaccinationCenter, "decision"), property
        )
        assert VaccinationCenter.decision.fset is not None, "decision must have setter"
