#!/usr/bin/env python3
"""
كيان مجال: تقرير الجهاز

✅ Domain Object حقيقي (ليس DTO)
✅ يستخدم في Use Cases ويعود للطبقات العليا
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone


@dataclass(frozen=True)
class DeviceReport:
    """
    كائن مجال (Domain Object) لتقرير الجهاز.
    
    هذا يحل مشكلة dict vs object في الاختبارات.
    يتبع مبدأ: Use Cases تعيد Domain Objects، وليس dicts.
    """
    device_id: str
    status: str
    generated_at: str
    report_data: Optional[dict] = None
    
    @classmethod
    def create(cls, device_id: str, status: str = 'generated', 
               report_data: Optional[dict] = None) -> 'DeviceReport':
        """مصنع لإنشاء تقرير جديد"""
        return cls(
            device_id=device_id,
            status=status,
            generated_at=datetime.now(timezone.utc).isoformat(),
            report_data=report_data
        )
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس للاستخدام في الطبقات العليا (CLI/API)"""
        from dataclasses import asdict
        return asdict(self)