"""اختبارات التحقق من DTOs — محدّثة لاستخدام Enum"""
import pytest
import dataclasses
from src.application.dtos.device_report_dto import DeviceReportDTO, ReportDecision, VVMStage
from src.application.dtos.center_report_dto import CenterReportDTO


class TestDeviceReportDTO:
    """اختبارات DeviceReportDTO"""
    
    def test_valid_dto_creation(self):
        """إنشاء ناجح بقيم صحيحة — باستخدام Enum"""
        dto = DeviceReportDTO(
            device_id='DEV_001',
            center_id='CTR_001',
            center_name='Test Center',
            temperature_ranges={'min': 2.0, 'max': 8.0},
            decision=ReportDecision.ACCEPTED,  # ✅ Enum بدلاً من string
            vvm_stage=VVMStage.A                # ✅ Enum بدلاً من string
        )
        assert dto.device_id == 'DEV_001'
        assert dto.decision == ReportDecision.ACCEPTED
        assert dto.vvm_stage == VVMStage.A
    
    def test_dto_is_frozen(self):
        """التحقق من أن DTO مجمد (غير قابل للتعديل)"""
        dto = DeviceReportDTO(
            device_id='DEV_001',
            center_id='CTR_001',
            center_name='Test',
            temperature_ranges={'min': 2.0, 'max': 8.0},
            decision=ReportDecision.ACCEPTED,
            vvm_stage=VVMStage.A
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            dto.device_id = 'MODIFIED'
    
    def test_empty_device_id_raises(self):
        """device_id فارغ يرفع ValueError"""
        with pytest.raises(ValueError):
            DeviceReportDTO(
                device_id='',
                center_id='CTR_001',
                center_name='Test',
                temperature_ranges={'min': 2, 'max': 8},
                decision=ReportDecision.ACCEPTED,
                vvm_stage=VVMStage.A
            )
    
    def test_invalid_temperature_range_raises(self):
        """min > max يرفع ValueError"""
        with pytest.raises(ValueError):
            DeviceReportDTO(
                device_id='DEV_001',
                center_id='CTR_001',
                center_name='Test',
                temperature_ranges={'min': 10, 'max': 5},  # ❌ min > max
                decision=ReportDecision.ACCEPTED,
                vvm_stage=VVMStage.A
            )
    
    def test_all_decision_values(self):
        """اختبار جميع قيم decision المسموحة"""
        for decision in ReportDecision:
            dto = DeviceReportDTO(
                device_id='DEV_001',
                center_id='CTR_001',
                center_name='Test',
                temperature_ranges={'min': 2, 'max': 8},
                decision=decision,
                vvm_stage=VVMStage.A
            )
            assert dto.decision == decision
    
    def test_all_vvm_stage_values(self):
        """اختبار جميع قيم VVMStage المسموحة"""
        for stage in VVMStage:
            dto = DeviceReportDTO(
                device_id='DEV_001',
                center_id='CTR_001',
                center_name='Test',
                temperature_ranges={'min': 2, 'max': 8},
                decision=ReportDecision.ACCEPTED,
                vvm_stage=stage
            )
            assert dto.vvm_stage == stage


class TestCenterReportDTO:
    """اختبارات CenterReportDTO"""
    
    def test_valid_center_dto_creation(self):
        """إنشاء ناجح لـ CenterReportDTO"""
        dto = CenterReportDTO(
            center_id='CTR_001',
            center_name='Test Center',
            total_devices=10,
            safe_devices=7,
            rejected_devices=2,
            partial_devices=1
        )
        assert dto.center_id == 'CTR_001'
        assert dto.total_devices == 10
    
    def test_center_dto_is_frozen(self):
        """التحقق من أن CenterReportDTO مجمد"""
        dto = CenterReportDTO(
            center_id='CTR_001',
            center_name='Test',
            total_devices=10,
            safe_devices=7,
            rejected_devices=2,
            partial_devices=1
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            dto.center_name = 'MODIFIED'
    
    def test_device_count_mismatch_raises(self):
        """مجموع الأجهزة لا يطابق total يرفع ValueError"""
        with pytest.raises(ValueError):
            CenterReportDTO(
                center_id='CTR_001',
                center_name='Test',
                total_devices=10,
                safe_devices=5,
                rejected_devices=2,
                partial_devices=1  # المجموع 8 ≠ 10
            )
    
    def test_empty_center_id_raises(self):
        """center_id فارغ يرفع ValueError"""
        with pytest.raises(ValueError):
            CenterReportDTO(
                center_id='',
                center_name='Test',
                total_devices=10,
                safe_devices=7,
                rejected_devices=2,
                partial_devices=1
            )
