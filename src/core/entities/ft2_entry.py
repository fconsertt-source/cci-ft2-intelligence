# src/models/ft2_entry.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class FT2Entry:
    """تمثيل لإدخال FT2 واحد (يوم واحد)"""
    day_number: int
    date: str
    temperatures: Dict[str, float]  # min, max, avg
    alarms: Dict[str, Dict[str, Any]]  # 0, 1
    sensor_timeout: Dict[str, Any]
    events: int
    
    @property
    def has_freezing(self) -> bool:
        """هل يوجد تجميد في هذا اليوم؟"""
        return self.alarms.get('0', {}).get('t_acc', 0) > 0
    
    @property
    def has_ccm_violation(self) -> bool:
        """هل يوجد انتهاك CCM في هذا اليوم؟"""
        return self.alarms.get('1', {}).get('t_acc', 0) > 600
    
    @property
    def freeze_minutes(self) -> int:
        """دقائق التجميد في هذا اليوم"""
        return self.alarms.get('0', {}).get('t_acc', 0)
    
    @property
    def ccm_minutes(self) -> int:
        """دقائق CCM في هذا اليوم"""
        return self.alarms.get('1', {}).get('t_acc', 0)
    
    @property
    def temperature_range(self) -> float:
        """مدى درجة الحرارة اليومي"""
        min_temp = self.temperatures.get('min', 0)
        max_temp = self.temperatures.get('max', 0)
        return max_temp - min_temp
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'day_number': self.day_number,
            'date': self.date,
            'temperatures': self.temperatures,
            'alarms': self.alarms,
            'sensor_timeout': self.sensor_timeout,
            'events': self.events,
            'has_freezing': self.has_freezing,
            'has_ccm_violation': self.has_ccm_violation,
            'freeze_minutes': self.freeze_minutes,
            'ccm_minutes': self.ccm_minutes,
            'temperature_range': self.temperature_range
        }