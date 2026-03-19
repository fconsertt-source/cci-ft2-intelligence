def test_temperature_exposure_is_pure_concept():
    """التحقق من أن النموذج المفاهيمي لا يحتوي على تفاصيل تنفيذ"""
    from src.domain.models.temperature_exposure import TemperatureExposure

    exposure = TemperatureExposure(temperature=15.0, duration_minutes=24.0)

    # 🔒 الحماية ضد الانزلاق المعماري
    assert not hasattr(
        exposure, "start_time"
    ), "TemperatureExposure must NOT contain start_time (Domain purity violation)"
    assert not hasattr(
        exposure, "end_time"
    ), "TemperatureExposure must NOT contain end_time (Domain purity violation)"
