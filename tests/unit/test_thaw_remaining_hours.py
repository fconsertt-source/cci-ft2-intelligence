# tests/unit/test_thaw_remaining_hours.py
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from src.application.dtos.device_report_dto import DeviceReportDTO, ReportDecision, VVMStage
from src.application.use_cases.requests import GenerateDeviceReportRequest
from src.application.use_cases.generate_device_report_uc import GenerateDeviceReportUseCase
from src.domain.value_objects.vaccine_specification import VaccineSpecification
from src.domain.entities.thermal_record import ThermalRecord
from src.domain.enums.regulatory_status import RegulatoryStatus


class TestThawRemainingHoursCalculation(unittest.TestCase):
    """اختبارات دالة execute لضمان حساب thaw_remaining_hours بشكل صحيح"""

    def setUp(self):
        """إعداد كائن use_case مع جميع التبعيات الوهمية (mocks)"""
        # 1. إنشاء Mock objects لجميع التبعيات المطلوبة
        self.mock_device_repo = Mock()
        self.mock_vaccine_specs = Mock()
        self.mock_regulatory_service = Mock()
        self.mock_estimator = Mock()
        self.mock_validator = Mock()
        self.mock_license_guard = Mock()

        # تأكد من أن license_guard.ensure_active() لا يسبب مشكلة
        self.mock_license_guard.ensure_active = Mock()

        # 2. إنشاء الـ UseCase مع تمرير جميع التبعيات
        self.use_case = GenerateDeviceReportUseCase(
            device_repository=self.mock_device_repo,
            vaccine_specifications=self.mock_vaccine_specs,
            regulatory_decision_service=self.mock_regulatory_service,
            estimator=self.mock_estimator,
            validator=self.mock_validator,
            license_guard=self.mock_license_guard
        )

        # تعطيل الـ ledger writer و validator (اختياري للاختبار)
        self.use_case._ledger_writer = None
        self.use_case._validator = None  # تم تعطيله مسبقاً لكن نؤكد

        # إعداد بيانات وهمية للتيملاين (timeline)
        self.mock_records = [
            Mock(spec=ThermalRecord, timestamp=datetime.now(), temperature=5.0, duration_minutes=30),
            Mock(spec=ThermalRecord, timestamp=datetime.now(), temperature=8.0, duration_minutes=15),
        ]

        # إعداد spec وهمي للقاح
        self.mock_spec = Mock(spec=VaccineSpecification)
        self.mock_spec.vaccine_type = "MenA"
        self.mock_spec.rationale = None
        self.mock_spec.shelf_life_hours = 17520  # سنتان = 17520 ساعة

        # إعداد نتيجة تقييم regulatory
        self.mock_excursions = []
        self.final_status = RegulatoryStatus.SAFE.name

        # إعداد advisory_info وهمي
        self.advisory_info = {
            "cumulative_impact": 0.0,
            "remaining_shelf_life": 50.0,  # 50% متبقي
        }

        # 3. تطبيق التصحيحات (patches) على الطرق الداخلية للـ use_case
        self.patcher_retrieve = patch.object(
            self.use_case, "_retrieve_device_timeline", return_value=self.mock_records
        )
        self.patcher_spec = patch.object(
            self.use_case, "_fetch_vaccine_specification", return_value=self.mock_spec
        )
        self.patcher_evaluate = patch.object(
            self.use_case, "_evaluate_timeline_regulatory",
            return_value=(self.mock_excursions, self.final_status)
        )
        self.patcher_estimator = patch.object(
            self.use_case._estimator, "calculate_cumulative_impact",
            return_value=self.advisory_info
        )
        # ملاحظة: ConfigLoader هو استيراد مباشر، نستخدم patch على الوحدة
        self.patcher_config = patch("src.application.use_cases.generate_device_report_uc.ConfigLoader.get", return_value=50)

        # بدء التصحيحات
        self.mock_retrieve = self.patcher_retrieve.start()
        self.mock_spec_method = self.patcher_spec.start()
        self.mock_evaluate = self.patcher_evaluate.start()
        self.mock_calc_impact = self.patcher_estimator.start()
        self.mock_config = self.patcher_config.start()

        # تنظيف التصحيحات بعد كل اختبار
        self.addCleanup(self.patcher_retrieve.stop)
        self.addCleanup(self.patcher_spec.stop)
        self.addCleanup(self.patcher_evaluate.stop)
        self.addCleanup(self.patcher_estimator.stop)
        self.addCleanup(self.patcher_config.stop)

    # ========== الاختبارات ==========

    def test_thaw_remaining_hours_calculation_with_shelf_life_hours(self):
        """اختبار حساب thaw_remaining_hours عندما يكون spec.shelf_life_hours موجوداً"""
        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 8760.0  # 50% من 17520
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="thaw_remaining_hours should be 8760.0 for 50% of 2-year shelf life"
        )

    def test_thaw_remaining_hours_calculation_without_shelf_life_hours(self):
        """اختبار عندما لا يكون spec.shelf_life_hours موجوداً -> استخدام القيمة الافتراضية (سنتان = 17520 ساعة)"""
        # إزالة الخاصية shelf_life_hours من الـ mock spec
        if hasattr(self.mock_spec, 'shelf_life_hours'):
            del self.mock_spec.shelf_life_hours

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 8760.0  # 50% من 17520
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="Without shelf_life_hours, default 2 years should be used"
        )

    def test_thaw_remaining_hours_with_different_remaining_percentage(self):
        """اختبار قيم مختلفة للنسبة المتبقية (25%)"""
        self.advisory_info["remaining_shelf_life"] = 25.0
        self.mock_calc_impact.return_value = self.advisory_info

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 4380.0  # 25% من 17520
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="25% of 2 years should be 4380 hours"
        )

    def test_thaw_remaining_hours_with_full_shelf_life(self):
        """اختبار النسبة 100%"""
        self.advisory_info["remaining_shelf_life"] = 100.0
        self.mock_calc_impact.return_value = self.advisory_info

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 17520.0
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="100% remaining should equal total shelf life hours"
        )

    def test_thaw_remaining_hours_with_zero_percent(self):
        """اختبار النسبة 0%"""
        self.advisory_info["remaining_shelf_life"] = 0.0
        self.mock_calc_impact.return_value = self.advisory_info

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 0.0
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="0% remaining should be 0 hours"
        )

    def test_thaw_remaining_hours_with_custom_shelf_life_hours(self):
        """اختبار باستخدام عمر لقاح مختلف (مثل HepB: 4 سنوات = 35040 ساعة)"""
        self.mock_spec.shelf_life_hours = 35040  # 4 سنوات
        self.advisory_info["remaining_shelf_life"] = 25.0
        self.mock_calc_impact.return_value = self.advisory_info

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 8760.0  # 25% of 35040 = 8760
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="25% of 4-year shelf life should be 8760 hours (1 year)"
        )

    def test_thaw_remaining_hours_with_missing_shelf_life_hours_and_no_attr(self):
        """اختبار حالة عدم وجود الخاصية shelf_life_hours نهائياً (hasattr=False)"""
        if hasattr(self.mock_spec, 'shelf_life_hours'):
            delattr(self.mock_spec, 'shelf_life_hours')

        request = GenerateDeviceReportRequest(device_id="FT2-12345")
        report = self.use_case.execute(request)

        expected_hours = 8760.0  # 50% of default 17520
        self.assertAlmostEqual(
            report.thaw_remaining_hours, expected_hours, places=2,
            msg="When shelf_life_hours missing, default 2 years should be used"
        )


if __name__ == '__main__':
    unittest.main()