"""
اختبارات وحدة لسياسة الاحتفاظ
"""

import pytest
from datetime import datetime, timezone, timedelta

from src.domain.entities.retention_policy import RetentionPolicy


class TestRetentionPolicy:
    """اختبارات سياسة الاحتفاظ"""
    
    def test_default_policy(self):
        """يجب إنشاء سياسة افتراضية صحيحة"""
        policy = RetentionPolicy()
        
        assert policy.default_retention_days == 90
        assert policy.min_retention_days == 30
        assert policy.max_retention_days == 365
    
    def test_calculate_expiry(self):
        """يجب حساب تاريخ الانتهاء بشكل صحيح"""
        policy = RetentionPolicy(default_retention_days=90)
        
        expiry = policy.calculate_expiry()
        expiry_date = datetime.fromisoformat(expiry)
        expected = datetime.now(timezone.utc) + timedelta(days=90)
        
        # السماح بهامش خطأ صغير
        assert abs((expiry_date - expected).total_seconds()) < 60
    
    def test_is_valid_retention(self):
        """يجب التحقق من صحة مدة الاحتفاظ"""
        policy = RetentionPolicy()
        
        assert policy.is_valid_retention(30) is True
        assert policy.is_valid_retention(90) is True
        assert policy.is_valid_retention(365) is True
        assert policy.is_valid_retention(29) is False
        assert policy.is_valid_retention(366) is False
    
    def test_override_retention(self):
        """يجب تجاوز المدة للأجهزة الحرجة"""
        policy = RetentionPolicy()
        
        # جهاز عادي
        assert policy.override_retention("130600112764") == 90
        
        # جهاز حرج
        assert policy.override_retention("CRITICAL_130600112764") == 365
