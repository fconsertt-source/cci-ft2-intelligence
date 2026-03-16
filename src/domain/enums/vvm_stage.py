# src/domain/enums/vvm_stage.py
from enum import Enum


class VVMStage(Enum):
    """مراحل نافذة المراقبة المرئية (VVM) — نسخة متوافقة مع الكود الحالي."""
    
    NONE = 1
    A = 2
    B = 3
    C = 4
    D = 5
    
    @property
    def is_usable(self) -> bool:
        """
        اللقاح صالح للاستخدام حتى المرحلة B (VVM2 مكافئ).
        C و D = التخلص فوراً.
        """
        return self in (VVMStage.NONE, VVMStage.A, VVMStage.B)
    
    @property
    def is_critical(self) -> bool:
        """مرحلة حرجة (يجب التخلص)."""
        return self in (VVMStage.C, VVMStage.D)
    
    @property
    def label_ar(self) -> str:
        """تسمية عربية للعرض."""
        return {
            VVMStage.NONE: "لا تعرض",
            VVMStage.A: "مرحلة A",
            VVMStage.B: "مرحلة B",
            VVMStage.C: "مرحلة C",
            VVMStage.D: "مرحلة D",
        }[self]

    @classmethod
    def from_duration(cls, minutes: float) -> "VVMStage":
        """تحديد المرحلة بناءً على المدة التراكمية"""
        days = minutes / (24 * 60)

        if days >= 14:
            return cls.D
        elif days >= 11:
            return cls.C
        elif days >= 6:
            return cls.B
        elif days >= 2:
            return cls.A
        else:
            return cls.NONE

    def get_color(self) -> str:
        """لون المؤشر في الواجهة"""
        return {
            self.NONE: "#4CAF50",  # أخضر
            self.A: "#FFC107",  # أصفر
            self.B: "#FF9800",  # برتقالي
            self.C: "#F44336",  # أحمر
            self.D: "#B71C1C",  # أحمر غامق
        }[self]
