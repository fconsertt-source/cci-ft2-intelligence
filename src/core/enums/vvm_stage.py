# src/core/enums/vvm_stage.py
from enum import Enum

class VVMStage(Enum):
    """مراحل نافذة المراقبة المرئية (VVM)"""
    NONE = "NONE"        # لا تعرض حراري مهم
    A = "A"              # 2-3 أيام فوق 8°C
    B = "B"              # 6-8 أيام فوق 8°C
    C = "C"              # 11-14 يوم فوق 8°C
    D = "D"              # >14 يوم أو حرارة شديدة
    
    @classmethod
    def from_duration(cls, minutes: float) -> 'VVMStage':
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
            self.A: "#FFC107",     # أصفر
            self.B: "#FF9800",     # برتقالي
            self.C: "#F44336",     # أحمر
            self.D: "#B71C1C"      # أحمر غامق
        }[self]