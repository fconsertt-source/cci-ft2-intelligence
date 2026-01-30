from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional, Dict


@dataclass
class Vaccine:
    """
    كيان يمثل لقاحًا واحدًا وقواعد تحمله الحراري المتطورة (v1.1.0)
    """
    id: str
    name: str
    full_loss_threshold_low: float
    full_loss_threshold_high: float
    shelf_life_days: int

    # (Temperature °C, Max exposure minutes) - legacy
    reference_table: List[Tuple[float, int]]
    
    # VVM Q10 Model Parameters
    q10_value: float = 2.0
    ideal_temp: float = 5.0

    # New Fields (Plan v1.1.0)
    category: str = "freeze_sensitive"
    is_freeze_stable: bool = False
    vvm_type: str = "VVM14"
    ultra_cold_chain_required: bool = False
    
    # Thaw & UCC Tracking
    thaw_start_time: Optional[datetime] = None
    thaw_duration_days: int = 0
    
    # Recommendations & Metadata
    actions: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, any]] = None

    def get_critical_limit(self) -> float:
        """يعيد الحد الحراري الحرج بناءً على خصائص اللقاح"""
        return self.full_loss_threshold_high
