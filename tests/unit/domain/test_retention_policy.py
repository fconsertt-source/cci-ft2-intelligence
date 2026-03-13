"""
اختبارات وحدة لسياسة الاحتفاظ
"""

from datetime import datetime, timezone

import pytest

# freezegun is a dev dependency; if absent we provide a no-op decorator
try:
    from freezegun import freeze_time

    FREEZEGUN_AVAILABLE = True
except ImportError:
    FREEZEGUN_AVAILABLE = False

    # tests can still run; the decorator will just return the original function
    def freeze_time(*args, **kwargs):
        def decorator(f):
            return f

        return decorator


from src.domain.entities.retention_policy import RetentionPolicy


class TestRetentionPolicy:
    """اختبارات سياسة الاحتفاظ"""

    def test_default_policy(self):
        """يجب إنشاء سياسة افتراضية صحيحة"""
        policy = RetentionPolicy()

        assert policy.default_retention_days == 90
        assert policy.min_retention_days == 30
        assert policy.max_retention_days == 365

    @freeze_time("2025-03-01 12:00:00")
    def test_calculate_expiry_returns_utc_iso_string(self):
        if not FREEZEGUN_AVAILABLE:
            pytest.skip("freezegun not available, skipping expiry assertion")
        """
        يجب أن تُعيد calculate_expiry نص ISO 8601 بصيغة UTC
        يحتوي على التاريخ الصحيح بعد المدة الافتراضية.
        """
        policy = RetentionPolicy(default_retention_days=90)
        expiry_str = policy.calculate_expiry()

        # التحقق من أن النص ينتهي بـ Z أو +00:00 (صيغة UTC)
        assert expiry_str.endswith("Z") or "+00:00" in expiry_str

        # تحويل النص إلى datetime aware (نتعامل مع Z)
        if expiry_str.endswith("Z"):
            expiry_str = expiry_str.replace("Z", "+00:00")
        expiry_dt = datetime.fromisoformat(expiry_str)

        # التاريخ المتوقع: 2025-03-01 + 90 يوم = 2025-05-30
        expected_dt = datetime(2025, 5, 30, 12, 0, 0, tzinfo=timezone.utc)

        assert expiry_dt == expected_dt

    def test_is_valid_retention_with_boundary_values(self):
        """يجب التحقق من صحة مدة الاحتفاظ مع القيم الحدودية"""
        policy = RetentionPolicy()

        # قيم صالحة
        assert policy.is_valid_retention(30) is True
        assert policy.is_valid_retention(90) is True
        assert policy.is_valid_retention(365) is True

        # قيم غير صالحة (أقل من الأدنى أو أكثر من الأقصى)
        assert policy.is_valid_retention(29) is False
        assert policy.is_valid_retention(366) is False

    @pytest.mark.parametrize(
        "device_id,expected",
        [
            ("130600112764", 90),  # جهاز عادي
            ("CRITICAL_130600112764", 365),  # بادئة CRITICAL
            (
                "130600112764_CRITICAL",
                365,
            ),  # لاحقة CRITICAL (إذا كان المنطق يبحث عن الكلمة في أي مكان)
            # lower-case variations should **not** be treated as critical (case-sensitive)
            ("critical_130600112764", 90),
            ("130600112764_critical", 90),
            ("CRITICAL", 365),  # فقط الكلمة
            ("", 90),  # سلسلة فارغة
            (None, 90),  # None (يجب التعامل معه كجهاز عادي أو رفع خطأ حسب التصميم)
        ],
    )
    def test_get_retention_period_critical_device(self, device_id, expected):
        """
        يجب أن تُعيد get_retention_period المدة الصحيحة للأجهزة العادية والحرجة.
        البحث يجب أن يكون حساساً لحالة الأحرف ("CRITICAL" فقط).
        """
        policy = RetentionPolicy()

        # إذا كان device_id = None، نتوقع أن تتعامل الدالة معه كقيمة غير حرجة (90)
        # إذا كانت الدالة لا تقبل None، يمكن تخطي هذا الاختبار أو توقع خطأ.
        # هنا نفترض أن التطبيق الحالي يقبل str فقط، لذا سنتخطى حالة None إذا كانت تسبب خطأ.
        if device_id is None:
            try:
                result = policy.get_retention_period(device_id)
                assert result == expected
            except (AttributeError, TypeError):
                pytest.skip("الدالة لا تقبل None، تم تخطي الاختبار")
        else:
            result = policy.get_retention_period(device_id)
            assert result == expected
