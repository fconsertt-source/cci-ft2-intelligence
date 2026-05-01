from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AnalysisResult:
    """
    النتيجة الموحدة لتحليل التعرض الحراري.
    تُستبدل القاموس الخام (dict) لتوفير Type Safety والتنبؤ بالأخطاء.
    """
    # المؤشرات الأساسية
    her_ratio: float
    ccm_index: str  # "0", "A", "B", "C", "ABC", "D"
    
    # Circuit breakers (قواطع الدائرة للقرارات الفورية)
    has_freeze: bool
    has_critical_heat: bool
    circuit_breaker: Optional[str]  # e.g., "FREEZE_EXCURSION", "CRITICAL_HEAT_34C" أو None
    
    # إحصاءات حرارية عامة (مفيدة للتقارير)
    max_temp: float
    min_temp: float
    total_hours_above_10: float
    total_hours_above_34: float

    @property
    def is_circuit_broken(self) -> bool:
        return self.circuit_breaker is not None