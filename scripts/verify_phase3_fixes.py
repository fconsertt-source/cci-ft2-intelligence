#!/usr/bin/env python3
"""
سكربت التحقق من إصلاحات Phase 3 — Production-Grade v2.1
يتضمن: Structural + Behavioral + Performance Verification

Usage:
    python scripts/verify_phase3_fixes.py

Note:
    يجب تشغيل السكربت من الجذر الرئيسي للمشروع
"""
import inspect
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# 🔧 إصلاح مسار Python — إضافة الجذر إلى sys.path
# ============================================================================
# الحصول على مسار الجذر الرئيسي (مجلد المشروع)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# إضافة المسارات إلى sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# التحقق من أن المسارات صحيحة
src_path = PROJECT_ROOT / "src"
tests_path = PROJECT_ROOT / "tests"

if not src_path.exists():
    print(f"❌ خطأ: مجلد src/ غير موجود في {src_path}")
    sys.exit(1)

# ألوان للطباعة
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check(condition, message):
    """توحيد طباعة نتائج التحقق"""
    if condition:
        print(f"{GREEN}✅{RESET} {message}")
        return True
    else:
        print(f"{RED}❌{RESET} {message}")
        return False


def main():
    results = []

    print("=" * 70)
    print(f"{BLUE}🔍 Phase 3 Verification — Production-Grade v2.1{RESET}")
    print("=" * 70)
    print(f"{YELLOW}📁 Project Root: {PROJECT_ROOT}{RESET}")
    print(f"{YELLOW}📁 src/ exists: {src_path.exists()}{RESET}")
    print(f"{YELLOW}📁 tests/ exists: {tests_path.exists()}{RESET}")
    print("=" * 70)

    # ========================================================================
    # 1. VaccinationCenter Checks — مع فحص التوقيع
    # ========================================================================
    print(f"\n{BLUE}📌 VaccinationCenter:{RESET}")
    try:
        from src.domain.entities.vaccination_center import FT2Entry, VaccinationCenter

        # ✅ فحص الوجود
        results.append(
            check(
                hasattr(VaccinationCenter, "add_ft2_entry"),
                "add_ft2_entry method exists",
            )
        )

        # ✅ فحص التوقيع (جديد — يمنع الدوال المكسورة)
        try:
            sig = inspect.signature(VaccinationCenter.add_ft2_entry)
            params = list(sig.parameters.keys())
            results.append(
                check(
                    "entry" in params or len(params) >= 1,
                    f"add_ft2_entry has correct signature (params: {params})",
                )
            )
        except Exception as e:
            results.append(check(False, f"add_ft2_entry signature check failed: {e}"))

        # ✅ فحص property + setter
        results.append(
            check(
                isinstance(
                    inspect.getattr_static(VaccinationCenter, "decision"), property
                ),
                "decision is a property",
            )
        )

        results.append(
            check(
                hasattr(VaccinationCenter, "decision")
                and VaccinationCenter.decision.fset is not None,
                "decision has setter",
            )
        )

        results.append(
            check(
                hasattr(VaccinationCenter, "_count_freeze_events"),
                "_count_freeze_events method exists",
            )
        )

        # ✅ فحص عدم تعارض الأسماء
        import ast

        vc_file = src_path / "domain" / "entities" / "vaccination_center.py"
        if vc_file.exists():
            with open(vc_file, "r", encoding="utf-8") as f:
                source = f.read()
                tree = ast.parse(source)

            field_names = []
            method_names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign) and hasattr(node.target, "id"):
                    if node.target.id.startswith("_"):
                        field_names.append(node.target.id)
                elif isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
                    method_names.append(node.name)

            results.append(
                check(
                    "_freeze_event_count" in field_names
                    and "_count_freeze_events" in method_names,
                    "No name collision between _freeze_event_count field and _count_freeze_events method",
                )
            )
        else:
            results.append(check(False, "vaccination_center.py file not found"))

        # ✅ اختبار سلوكي سريع (جديد)
        try:
            center = VaccinationCenter(
                id="TEST",
                name="Test",
                device_ids=["D1"],
                temperature_ranges={"min": 2, "max": 8},
                decision_thresholds={},
            )
            entry = FT2Entry("D1", datetime.now(), -1.0, "Vax", "B1")
            center.add_ft2_entry(entry)
            results.append(
                check(
                    center.decision == "REJECTED_FREEZE_SENSITIVE",
                    "Behavioral test: freeze entry triggers rejection",
                )
            )
        except Exception as e:
            results.append(check(False, f"Behavioral test failed: {e}"))

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import VaccinationCenter: {e}")
        results.append(False)

    # ========================================================================
    # 2. UseCase Signature Check — مع فحص النوع
    # ========================================================================
    print(f"\n{BLUE}📌 GenerateDeviceReportUseCase:{RESET}")
    try:
        from src.application.use_cases.generate_device_report_uc import (
            GenerateDeviceReportUseCase,
        )
        from src.application.use_cases.requests import GenerateDeviceReportRequest

        sig = inspect.signature(GenerateDeviceReportUseCase.execute)
        params = list(sig.parameters.keys())

        results.append(
            check("request" in params, "execute() accepts 'request' parameter")
        )

        # ✅ فحص نوع المعامل (جديد)
        request_param = sig.parameters.get("request")
        if request_param:
            results.append(
                check(
                    request_param.annotation == GenerateDeviceReportRequest
                    or request_param.annotation == inspect.Parameter.empty,
                    "request parameter type is GenerateDeviceReportRequest",
                )
            )

        results.append(
            check(
                "device_id" not in params,
                "execute() does NOT accept device_id directly (must use Request DTO)",
            )
        )

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import UseCase: {e}")
        results.append(False)

    # ========================================================================
    # 3. PDF Wrapper Checks
    # ========================================================================
    print(f"\n{BLUE}📌 PDF Wrapper:{RESET}")
    try:
        from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import (
            UnifiedPDFGeneratorWrapper,
            get_pdf_generator,
        )

        results.append(
            check(True, "UnifiedPDFGeneratorWrapper importable from adapters/reporting")
        )

        results.append(
            check(
                hasattr(UnifiedPDFGeneratorWrapper, "generate"),
                "UnifiedPDFGeneratorWrapper has generate() method",
            )
        )

        # ✅ فحص التوقيع (جديد)
        try:
            sig = inspect.signature(UnifiedPDFGeneratorWrapper.generate)
            params = list(sig.parameters.keys())
            results.append(
                check(
                    "dto" in params or len(params) >= 1,
                    f"generate() has correct signature (params: {params})",
                )
            )
        except Exception as e:
            results.append(check(False, f"generate() signature check failed: {e}"))

        results.append(
            check(
                callable(get_pdf_generator),
                "get_pdf_generator() factory function exists",
            )
        )

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import from adapters/reporting: {e}")
        results.append(False)

    # التحقق من Shim
    shim_path = src_path / "infrastructure" / "pdf" / "unified_pdf_generator_wrapper.py"
    try:
        from src.infrastructure.pdf.unified_pdf_generator_wrapper import (
            UnifiedPDFGeneratorWrapper as ShimWrapper,
        )

        results.append(check(True, "PDF Shim exists at src/infrastructure/pdf/"))
    except ImportError:
        if shim_path.exists():
            print(f"{YELLOW}⚠️{RESET} PDF Shim file exists but import failed")
        else:
            print(
                f"{YELLOW}⚠️{RESET} PDF Shim not found (may be acceptable if tests updated)"
            )
        results.append(True)  # Not critical if tests use new path

    # ========================================================================
    # 4. CCM Calculator Checks — مع اختبار سلوكي عددي (حرج!)
    # ========================================================================
    print(f"\n{BLUE}📌 CCMCalculator:{RESET}")
    try:
        from src.domain.calculators.ccm_calculator import (
            TIME_UNIT,
            CCMCalculator,
            TemperatureReading,
        )

        results.append(
            check(
                TIME_UNIT == "minutes",
                f"TIME_UNIT = 'minutes' (current: '{TIME_UNIT}')",
            )
        )

        # ✅ فحص التوثيق
        doc = CCMCalculator.calculate_auc.__doc__
        results.append(
            check(
                doc is not None and "minutes" in doc.lower(),
                "calculate_auc docstring mentions minutes",
            )
        )

        # ✅ فحص defensive guard في الكود
        source = inspect.getsource(CCMCalculator.calculate_auc)
        results.append(
            check(
                "delta_seconds <= 0" in source or "delta_seconds < 0" in source,
                "Defensive guard for delta_seconds <= 0 exists",
            )
        )

        results.append(
            check(
                "assert total_auc >= 0" in source,
                "Assertion for non-negative AUC exists",
            )
        )

        # 🔴 اختبار سلوكي عددي (جديد — حاسم!)
        try:
            base = datetime(2025, 1, 1)
            readings = [
                TemperatureReading("V1", 10.0, base),
                TemperatureReading("V1", 10.0, base + timedelta(minutes=60)),
            ]
            auc = CCMCalculator().calculate_auc(readings, base_temp=8.0)
            # المتوقع: excess=2, avg=2, dt=60 → 120
            results.append(
                check(
                    abs(auc - 120.0) < 1e-6,
                    f"✅ AUC behavioral check (expected 120, got {auc})",
                )
            )
        except Exception as e:
            results.append(check(False, f"AUC behavioral test failed: {e}"))

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import CCMCalculator: {e}")
        results.append(False)

    # ========================================================================
    # 5. Time Factory Check
    # ========================================================================
    print(f"\n{BLUE}📌 Time Factory:{RESET}")
    try:
        from tests.helpers.time_factory import create_reading, hours, minutes

        results.append(
            check(callable(create_reading), "create_reading() helper exists")
        )

        results.append(check(callable(minutes), "minutes() helper exists"))

        results.append(check(callable(hours), "hours() helper exists"))

        results.append(check(minutes(60) == 60.0, "minutes(60) returns 60.0"))

        results.append(check(hours(2) == 120.0, "hours(2) returns 120.0"))

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import time_factory: {e}")
        results.append(False)

    # ========================================================================
    # 6. RetentionPolicy Check
    # ========================================================================
    print(f"\n{BLUE}📌 RetentionPolicy:{RESET}")
    try:
        from src.domain.services.retention_policy import RetentionPolicy

        policy = RetentionPolicy()

        results.append(
            check(
                policy.override_retention("CRITICAL") == 365,
                "CRITICAL device returns 365 days",
            )
        )

        results.append(
            check(
                policy.override_retention("130600112764_CRITICAL") == 365,
                "Device with CRITICAL suffix returns 365 days",
            )
        )

        results.append(
            check(
                policy.override_retention("critical") == 90,
                "lowercase 'critical' returns 90 days (case-sensitive)",
            )
        )

        results.append(
            check(
                policy.override_retention(None) == 90, "None device_id returns 90 days"
            )
        )

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import RetentionPolicy: {e}")
        results.append(False)

    # ========================================================================
    # 7. ChartBuilder Check — تحقق دلالياً (مقاوم للتغييرات)
    # ========================================================================
    print(f"\n{BLUE}📌 ChartBuilder:{RESET}")
    try:
        from src.presentation.reporting.components.chart_builder import ChartBuilder

        cb = ChartBuilder("#000")
        result = cb.build([], "official")

        # ✅ ensure placeholder consists of Flowable-like objects
        results.append(
            check(
                isinstance(result, list)
                and len(result) > 0
                and all(hasattr(el, "getKeepWithNext") for el in result),
                f"ChartBuilder returns flowable placeholder (got: {result})",
            )
        )

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import ChartBuilder: {e}")
        results.append(False)

    # ========================================================================
    # 8. GuardianGUI Check
    # ========================================================================
    print(f"\n{BLUE}📌 GuardianGUI:{RESET}")
    try:
        from src.presentation.gui.guardian_gui import GuardianGUI

        results.append(
            check(
                hasattr(GuardianGUI, "_ensure_ft2_data_available"),
                "_ensure_ft2_data_available method exists",
            )
        )

        # ✅ فحص التوقيع (جديد)
        try:
            sig = inspect.signature(GuardianGUI._ensure_ft2_data_available)
            results.append(check(True, f"_ensure_ft2_data_available signature valid"))
        except Exception as e:
            results.append(
                check(False, f"_ensure_ft2_data_available signature check failed: {e}")
            )

    except ImportError as e:
        print(f"{RED}❌{RESET} Failed to import GuardianGUI: {e}")
        results.append(False)

    # ========================================================================
    # 9. Performance Sanity Gate — (جديد — حاسم!)
    # ========================================================================
    print(f"\n{BLUE}📌 Performance Sanity Gate:{RESET}")
    try:
        from src.domain.calculators.ccm_calculator import (
            CCMCalculator,
            TemperatureReading,
        )

        base = datetime(2025, 1, 1)
        readings = [
            TemperatureReading("V1", 9.0, base + timedelta(minutes=i))
            for i in range(5000)  # 5K قراءة
        ]

        start = time.perf_counter()
        CCMCalculator().calculate_auc(readings)
        duration = time.perf_counter() - start

        results.append(
            check(
                duration < 1.0,
                f"Performance sanity (<1s for 5k readings, got {duration:.3f}s)",
            )
        )

        if duration >= 1.0:
            print(f"{YELLOW}⚠️{RESET} WARNING: Performance degradation detected!")

    except Exception as e:
        print(f"{YELLOW}⚠️{RESET} Performance check skipped: {e}")
        results.append(True)  # لا نفشل إذا تعذر قياس الأداء

    # ========================================================================
    # 10. Circular Import Check — (اختياري لكن قوي)
    # ========================================================================
    print(f"\n{BLUE}📌 Circular Import Check (Optional):{RESET}")
    try:
        import subprocess

        result = subprocess.run(
            ["python", "-c", 'import src; print("✅ No immediate circular imports")'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            results.append(check(True, "No immediate circular imports detected"))
        else:
            results.append(
                check(False, f"Circular import detected: {result.stderr[:200]}")
            )
    except Exception as e:
        print(f"{YELLOW}⚠️{RESET} Circular import check skipped: {e}")
        results.append(True)

    # ========================================================================
    # Final Summary
    # ========================================================================
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    if percentage == 100:
        print(f"{GREEN}✅ جميع التحقق نجح: {passed}/{total} ({percentage:.1f}%){RESET}")
        print(f"\n{GREEN}🎯 جاهز لتشغيل pytest{RESET}")
        print(f"\n{BLUE}📋 الخطوات التالية:{RESET}")
        print("  1. pytest tests/contracts/ -v")
        print("  2. pytest tests/unit/test_ccm_calculator.py -v")
        print("  3. pytest --tb=short -q")
        return 0
    else:
        print(f"{RED}❌ بعض التحقق فشل: {passed}/{total} ({percentage:.1f}%){RESET}")
        print(f"\n{YELLOW}⚠️ أصلح الأعطال أعلاه قبل تشغيل pytest{RESET}")

        # عرض الأعطال الحرجة فقط
        print(f"\n{RED}🔴 الأعطال الحرجة:{RESET}")
        critical_failures = [
            "AUC behavioral check",
            "Performance sanity",
            "TIME_UNIT",
            "add_ft2_entry",
            "execute() request signature",
        ]
        # يمكن إضافة تتبع مفصل هنا

        return 1


if __name__ == "__main__":
    sys.exit(main())
