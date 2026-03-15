# src/domain/enums/device_status.py
"""
DeviceStatus — حالة جهاز المراقبة الحرارية
"""
from __future__ import annotations
from enum import Enum


class DeviceStatus(Enum):
    """
    دورة حياة جهاز Fridge-tag 2 E.

    ACTIVE    → الجهاز يعمل ومرتبط بمعدة تبريد
    RETIRED   → انتهت صلاحيته أو توقف — لا يقبل بيانات جديدة
    REPLACED  → تم استبداله بجهاز جديد — السجل التاريخي محفوظ
    """
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    REPLACED = "REPLACED"