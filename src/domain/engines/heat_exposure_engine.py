# heat_exposure_engine.py (مُحسّن)
class HeatExposureEngine:
    def __init__(self, reference_table: List[Tuple[float, int]]):
        self.reference_table = sorted(reference_table, key=lambda x: x[0])
    
    def compute_her(self, temperature: float, exposure_minutes: int) -> float:
        full_duration = self._linear_interpolate_duration(temperature)
        her = exposure_minutes / full_duration if full_duration > 0 else 0
        return min(her, 1.0)
    
    def _linear_interpolate_duration(self, temp: float) -> float:
        """استيفاء خطي بين نقطتين في الجدول المرجعي"""
        if not self.reference_table:
            return 0
        
        # إذا كانت درجة الحرارة أقل من أو تساوي أول قيمة
        if temp <= self.reference_table[0][0]:
            return float(self.reference_table[0][1])
        
        # إذا كانت درجة الحرارة أكبر من أو تساوي آخر قيمة
        if temp >= self.reference_table[-1][0]:
            return float(self.reference_table[-1][1])
        
        # البحث عن الفترة المناسبة للاستيفاء
        for i in range(len(self.reference_table) - 1):
            temp_low, duration_low = self.reference_table[i]
            temp_high, duration_high = self.reference_table[i + 1]
            
            if temp_low <= temp <= temp_high:
                # الاستيفاء الخطي
                ratio = (temp - temp_low) / (temp_high - temp_low)
                interpolated = duration_low + ratio * (duration_high - duration_low)
                return interpolated
        
        return float(self.reference_table[-1][1])