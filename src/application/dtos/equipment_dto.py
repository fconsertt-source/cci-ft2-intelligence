"""
Equipment DTO — Application Layer
يمثل بيانات المعدة في مركز التطعيم.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.enums.device_status import DeviceStatus
from src.domain.enums.vvm_stage import VVMStage
from src.domain.entities.temperature_reading import TemperatureReading


@dataclass
class EquipmentDTO:
    """
    Data Transfer Object لمعدة مركز تطعيم.
    
    يستخدم لنقل البيانات بين الطبقات دون تسريب كيانات Domain.
    """
    # الحقول الأساسية (مطلوبة)
    equipment_id: str
    equipment_name: str
    device_id: str
    
    # الحقول الأساسية (اختيارية)
    center_id: Optional[str] = None
    equipment_type: str = "unknown"  # ← جعل اختيارياً مع قيمة افتراضية
    
    # نطاقات درجة الحرارة (قابلة للتكوين)
    min_temp: float = 2.0
    max_temp: float = 8.0
    temperature_ranges: Dict[str, Any] = field(default_factory=dict)
    
    # عتبات القرار (مطلوبة لـ Use Cases)
    decision_thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # حالة حالية
    status: DeviceStatus = DeviceStatus.ACTIVE
    vvm_stage: VVMStage = VVMStage.NONE
    
    # بيانات حرارية
    ft2_entries: List[TemperatureReading] = field(default_factory=list)
    
    # قرارات
    decision: Optional[str] = None
    decision_reasons: List[str] = field(default_factory=list)
    alert_level: str = "NONE"  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    
    # إحصائيات
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    stats: Optional[Dict[str, Any]] = None
    
    # وقت آخر تحديث
    last_updated: datetime = field(default_factory=datetime.now)
    
    # ===========================================================
    # Methods للربط مع FT2Linker
    # ===========================================================
    
    def add_ft2_entry(self, entry: TemperatureReading) -> None:
        """
        إضافة قراءة FT2 إلى المعدة.
        متوافق مع FT2Linker.link_generator()
        """
        self.ft2_entries.append(entry)
    
    def add_reading(self, reading: TemperatureReading) -> None:
        """اسم بديل لـ add_ft2_entry — للتوافق"""
        self.ft2_entries.append(reading)
    
    # ===========================================================
    # Properties مساعدة
    # ===========================================================
    
    @property
    def has_data(self) -> bool:
        """هل تحتوي المعدة على بيانات حرارية؟"""
        return len(self.ft2_entries) > 0
    
    @property
    def temperature_range_label(self) -> str:
        """تسمية نطاق الحرارة للعرض"""
        return f"{self.min_temp}°C إلى {self.max_temp}°C"
