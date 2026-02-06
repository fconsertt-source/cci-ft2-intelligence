import pytest
from datetime import datetime, timedelta

from src.application.use_cases.evaluate_cold_chain_safety_use_case import EvaluateColdChainSafetyUseCase
from src.application.dtos.evaluate_cold_chain_safety_request import (
    EvaluateColdChainSafetyRequest,
    TemperatureReading,
)
from src.application.dtos.analysis_result_dto import VaccineStatus


def make_dummy_readings(device_id: str, count: int = 3):
    """إنشاء قراءات حرارة وهمية بالترتيب الزمني"""
    now = datetime.now()
    return tuple(
        TemperatureReading(
            device_id=device_id,
            value=5.0 + i,  # درجة حرارة بسيطة متزايدة
            timestamp=now + timedelta(hours=i)
        )
        for i in range(count)
    )


def test_uc_creation_and_execute_returns_response():
    """التحقق من أن UseCase يعمل مع طلب صالح ويعيد استجابة متوقعة"""
    uc = EvaluateColdChainSafetyUseCase()

    # تجهيز البيانات الوهمية
    readings = make_dummy_readings("DEV001")

    request = EvaluateColdChainSafetyRequest(
        center_id="C01",
        center_name="Test Center",
        readings=readings,
    )

    # تنفيذ الـ UseCase
    response = uc.execute(request)

    # التحقق من أن الاستجابة تعكس الطلب والتحليل
    assert response.center_id == "C01"
    assert response.decision is not None
    assert response.stability_budget_consumed_pct >= 0.0


def test_uc_handles_empty_request():
    """التحقق من التعامل مع طلب فارغ"""
    uc = EvaluateColdChainSafetyUseCase()
    request = EvaluateColdChainSafetyRequest(center_id="C02", center_name="Empty Center", readings=())
    response = uc.execute(request)

    # يجب أن تكون النتيجة حالة غير معروفة ولكن بدون خطأ
    assert response.center_id == "C02"
    assert response.decision == "UNKNOWN"
