from typing import Iterable, List
from src.application.dtos.center_stats_dto import CenterStatsDTO

class CenterStatsService:
    """خدمة مسؤولة عن حساب الإحصائيات الفيزيائية من القراءات الخام"""
    
    def compute(self, center_id: str, ft2_entries: Iterable) -> CenterStatsDTO:
        # استخراج درجات الحرارة الصالحة
        # نستخدم getattr للحماية من اختلاف أسماء الحقول في الكائنات المختلفة
        entries_list = list(ft2_entries)
        temps: List[float] = [
            getattr(e, "temp", getattr(e, "temperature", None)) 
            for e in entries_list 
            if getattr(e, "temp", getattr(e, "temperature", None)) is not None
        ]

        print("DEBUG entry type:", type(ft2_entries[0]))
        
        avg_temp = sum(temps) / len(temps) if temps else None
        min_temp = min(temps) if temps else None
        max_temp = max(temps) if temps else None
        
        has_freeze = any(getattr(e, "freeze_duration", 0) > 0 for e in entries_list)
        has_any_heat_duration = any(getattr(e, "heat_duration", 0) > 0 for e in entries_list)
        
        return CenterStatsDTO(
            center_id=center_id,
            num_ft2_entries=len(entries_list),
            has_freeze=has_freeze,
            has_any_heat_duration=has_any_heat_duration,
            avg_temperature=avg_temp,
            min_temperature=min_temp,
            max_temperature=max_temp
        )