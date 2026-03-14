"""
اختبارات عقود معمارية — Production-Grade v3.0
✅ تستخدم __module__ بدلاً من file paths
✅ مقاومة لـ Windows/Linux/PyInstaller
"""

import inspect
from typing import get_type_hints

import pytest


class TestEntityUniqueness:
    """ضمان أن الكيانات النطاقية معرّفة مرة واحدة فقط"""

    def test_ft2entry_defined_in_domain_only(self):
        """
        ✅ FT2Entry يجب أن يكون معرّفاً في domain/entities فقط
        استخدام __module__ بدلاً من file path
        """
        from src.domain.entities.ft2_entry import FT2Entry

        # ✅ فحص module path (مستقر عبر المنصات)
        assert FT2Entry.__module__.startswith(
            "src.domain.entities"
        ), f"FT2Entry must be in src.domain.entities, found in: {FT2Entry.__module__}"

    def test_vaccination_center_defined_in_domain_only(self):
        """VaccinationCenter يجب أن يكون معرّفاً في domain/entities فقط"""
        from src.domain.entities.vaccination_center import VaccinationCenter

        assert VaccinationCenter.__module__.startswith(
            "src.domain.entities"
        ), f"VaccinationCenter must be in src.domain.entities, found in: {VaccinationCenter.__module__}"

    def test_no_infrastructure_domain_entity_definitions(self):
        """Infrastructure لا يجب أن يكيّن Domain Entities"""
        import ast
        from pathlib import Path

        infra_dir = Path("src/infrastructure")
        domain_entity_names = ["FT2Entry", "VaccinationCenter", "DeviceReportDTO"]

        for py_file in infra_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if node.name in domain_entity_names:
                            # استثناء: alias مع تحذير deprecation
                            with open(py_file, "r", encoding="utf-8") as f2:
                                content = f2.read()
                                if "DeprecationWarning" not in content:
                                    pytest.fail(
                                        f"Infrastructure cannot define domain entity "
                                        f"{node.name} in {py_file}"
                                    )


class TestDTOSourceOfTruth:
    """ضمان أن DTOs لها مصدر واحد للحقيقة"""

    def test_ft2_entry_dto_single_source(self):
        """FT2EntryDTO يجب أن يُستورد من مصدر واحد"""
        from src.domain.dtos.ft2_entry_dto import FT2EntryDTO

        assert FT2EntryDTO.__module__.startswith(
            "src.domain.dtos"
        ), f"FT2EntryDTO source must be in src.domain.dtos, found in: {FT2EntryDTO.__module__}"

    def test_device_report_dto_single_source(self):
        """DeviceReportDTO يجب أن يُستورد من مصدر واحد"""
        from src.application.dtos.device_report_dto import DeviceReportDTO

        assert DeviceReportDTO.__module__.startswith(
            "src.application.dtos"
        ), f"DeviceReportDTO source must be in src.application.dtos, found in: {DeviceReportDTO.__module__}"


class TestLayerBoundaries:
    """فحص حدود الطبقات المعمارية"""

    def test_domain_does_not_import_infrastructure(self):
        """Domain Layer لا يجب أن يستورد من Infrastructure"""
        import ast
        from pathlib import Path

        domain_dir = Path("src/domain")
        forbidden_imports = ["infrastructure", "presentation"]

        for py_file in domain_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            for forbidden in forbidden_imports:
                                if forbidden in node.module:
                                    pytest.fail(
                                        f"Domain layer cannot import from {forbidden}. "
                                        f"Violation in {py_file}: import from {node.module}"
                                    )

    def test_usecase_uses_request_dto_only(self):
        """UseCase.execute يجب أن يقبل Request DTO فقط"""
        from src.application.use_cases.generate_device_report_uc import (
            GenerateDeviceReportUseCase,
        )
        from src.application.use_cases.requests import GenerateDeviceReportRequest

        sig = inspect.signature(GenerateDeviceReportUseCase.execute)

        try:
            hints = get_type_hints(GenerateDeviceReportUseCase.execute)
            request_type = hints.get("request")
            assert (
                request_type == GenerateDeviceReportRequest
            ), f"request must be GenerateDeviceReportRequest, got: {request_type}"
        except Exception:
            # Fallback: فحص string annotation
            request_param = sig.parameters.get("request")
            if request_param:
                annotation = str(request_param.annotation)
                assert (
                    "GenerateDeviceReportRequest" in annotation
                ), f"request parameter must be GenerateDeviceReportRequest, got: {annotation}"
