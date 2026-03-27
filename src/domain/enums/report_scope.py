#!/usr/bin/env python3
"""
نطاقات التقارير - عقد موحد لأنواع التقارير
"""
from enum import Enum


class ReportScope(Enum):
    """نطاق التقرير يحدد مستوى التجميع"""

    DEVICE = "device"  # تقرير جهاز واحد
    DEVICE_RANGE = "device_range"  # تقرير فترة زمنية لجهاز
    CENTER = "center"  # تقرير مركز كامل (جميع الأجهزة)
    CYCLE = "cycle"  # تقرير دورة كاملة (جميع المراكز)


class ReportType(Enum):
    """نوع التقرير يحدد التنسيق والمحتوى"""

    OFFICIAL = "official"  # رسمي بتوقيعات وختم
    TECHNICAL = "technical"  # تقني بمخططات وجداول
    ARABIC = "arabic"  # عربي كامل مع RTL
    EXECUTIVE = "executive"  # ملخص تنفيذي للإدارة
