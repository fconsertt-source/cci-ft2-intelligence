"""
سياسة الاحتفاظ بالملفات - Domain Policy
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional


@dataclass(frozen=True)
class RetentionPolicy:
    """
    سياسة الاحتفاظ بالملفات.
    
    تحدد مدة الاحتفاظ لكل نوع من الملفات.
    قابلة للتوسع مستقبلاً لدعم سياسات مختلفة حسب الجهاز/النوع.
    """
    
    default_retention_days: int = 90
    min_retention_days: int = 30
    max_retention_days: int = 365
    
    def calculate_expiry(self, archived_at: Optional[str] = None) -> str:
        """
        حساب تاريخ الانتهاء بناءً على السياسة.
        
        Args:
            archived_at: تاريخ الأرشفة (ISO format)، أو الآن إذا لم يُحدد
            
        Returns:
            str: تاريخ الانتهاء بصيغة ISO
        """
        if archived_at:
            archive_date = datetime.fromisoformat(archived_at)
        else:
            archive_date = datetime.now(timezone.utc)
        
        expiry = archive_date + timedelta(days=self.default_retention_days)
        return expiry.isoformat()
    
    def is_valid_retention(self, days: int) -> bool:
        """
        التحقق من صحة مدة الاحتفاظ.
        
        Args:
            days: عدد أيام الاحتفاظ
            
        Returns:
            bool: True إذا كانت المدة صالحة
        """
        return self.min_retention_days <= days <= self.max_retention_days
    
    def override_retention(self, device_id: str) -> int:
        """
        تجاوز مدة الاحتفاظ الافتراضية لجهاز معين.
        
        يمكن توسيعها مستقبلاً لدعم قواعد معقدة.
        
        Args:
            device_id: معرف الجهاز
            
        Returns:
            int: عدد أيام الاحتفاظ للجهاز
        """
        # TODO: إضافة قواعد خاصة للأجهزة الحرجة
        # مثال: إذا device_id يبدأ بـ "CRITICAL_" → 365 يوم
        if device_id.startswith("CRITICAL_"):
            return 365
        return self.default_retention_days
