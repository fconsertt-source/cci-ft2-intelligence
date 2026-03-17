from datetime import datetime, timedelta

from src.application.use_cases.evaluate_cold_chain_safety_use_case import \
    EvaluateColdChainSafetyUseCase
from src.domain.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest, TemperatureReading)


class TestEvaluateColdChainSafetyUseCase:

    def test_execute_safe_readings(self):
        """اختبار سيناريو درجات حرارة سليمة (ضمن النطاق 2-8)"""
        # Arrange
        use_case = EvaluateColdChainSafetyUseCase()
        base_time = datetime(2024, 1, 1, 10, 0, 0)

        # توليد قراءات سليمة (بين 4.0 و 5.0)
        readings = tuple(
            TemperatureReading(
                value=4.0 + (i * 0.1),
                timestamp=base_time + timedelta(minutes=15 * i),
                device_id="DEV_SAFE",
            )
            for i in range(10)
        )

        request = EvaluateColdChainSafetyRequest(
            center_id="CENTER_SAFE",
            center_name="Safe Center",
            readings=readings,
            temperature_ranges={"min": 2.0, "max": 8.0},
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.center_id == "CENTER_SAFE"
        assert response.has_freeze is False
        assert response.has_ccm_violation is False
        # نتوقع أن يكون القرار مقبولاً أو غير مرفوض بناءً على القواعد الافتراضية
        assert response.decision != "UNKNOWN"

    def test_execute_freeze_violation(self):
        """اختبار سيناريو حدوث تجميد"""
        # Arrange
        use_case = EvaluateColdChainSafetyUseCase()
        base_time = datetime(2024, 1, 1, 10, 0, 0)

        readings_list = []
        # قراءات عادية
        for i in range(4):
            readings_list.append(
                TemperatureReading(
                    value=4.0,
                    timestamp=base_time + timedelta(minutes=15 * i),
                    device_id="DEV_FREEZE",
                )
            )

        # قراءات تجميد (أقل من -0.5 لفترة)
        for i in range(4):
            readings_list.append(
                TemperatureReading(
                    value=-2.0,
                    timestamp=base_time + timedelta(minutes=15 * (4 + i)),
                    device_id="DEV_FREEZE",
                )
            )

        request = EvaluateColdChainSafetyRequest(
            center_id="CENTER_FREEZE",
            center_name="Freeze Center",
            readings=tuple(readings_list),
            temperature_ranges={"min": 2.0, "max": 8.0},
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.has_freeze is True
        # يجب أن ينعكس التجميد على القرار (عادة REJECTED أو WARNING)
        assert "SAFE" not in response.decision and "ACCEPTED" not in response.decision

    def test_execute_empty_readings(self):
        """اختبار التعامل مع قائمة قراءات فارغة"""
        use_case = EvaluateColdChainSafetyUseCase()
        request = EvaluateColdChainSafetyRequest(
            center_id="C_EMPTY",
            center_name="Empty",
            readings=(),
            temperature_ranges={"min": 2, "max": 8},
        )

        response = use_case.execute(request)
        assert response.decision == "UNKNOWN"
