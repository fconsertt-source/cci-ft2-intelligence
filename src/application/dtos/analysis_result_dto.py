from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from src.core.enums.vvm_stage import VVMStage

class VaccineStatus(Enum):
    SAFE = "SAFE"
    PARTIAL = "PARTIAL"
    DISCARD = "DISCARD"

@dataclass
class AnalysisResultDTO:
    vaccine_id: str
    status: VaccineStatus
    her: float  # Heat Exposure Ratio
    ccm: float  # Cold Chain Monitor delta
    vvm_stage: VVMStage = VVMStage.NONE
    
    # New Fields (v1.1.0)
    alert_level: str = "GREEN"  # GREEN, YELLOW, RED
    category_display: str = ""
    thaw_remaining_hours: Optional[float] = None
    is_thawing: bool = False
    stability_budget_consumed_pct: float = 0.0
    
    decision_reasons: List[str] = field(default_factory=list)
    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def add_reason(self, reason: str, evidence: Dict[str, Any] = None):
        """إضافة سبب للقرار مع أدلة"""
        self.decision_reasons.append(reason)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "evidence": evidence or {},
            "status": self.status.value
        }
        self.audit_log.append(log_entry)
    
    def generate_recommendations(self):
        """
        Generates smart recommendations based on status, alert levels, and vaccine category (v1.1.0).
        """
        self.recommendations = []
        
        # 1. Base on Status
        if self.status == VaccineStatus.DISCARD:
            self.recommendations.append("❌ يتم استبعاد هذا اللقاح فوراً من الاستخدام.")
            self.recommendations.append("🚩 يجب التحقق من وحدة التبريد وإصلاح الخلل الفني.")
        elif self.status == VaccineStatus.PARTIAL:
            self.recommendations.append("⚠️ يستخدم هذا اللقاح مع الأولوية (استخدام أولاً).")
        
        # 2. Base on Alert Level
        if self.alert_level == "YELLOW":
            self.recommendations.append("🟡 تنبيه: استهلاك مرتفع للميزانية الحرارية.")
            
        # 3. Base on Thaw Info
        if self.thaw_remaining_hours is not None:
            days = round(self.thaw_remaining_hours / 24, 1)
            if days > 0:
                self.recommendations.append(f"📦 لقاح مذاب: متبقي {days} يوم في الصلاحية القصيرة.")
            else:
                self.recommendations.append("🚨 تلف: انقضاء صلاحية الثلاجة للقاح المذاب.")

        # 4. Specific VVM Stage recommendations
        if self.vvm_stage == VVMStage.C:
            self.recommendations.append("🔔 مؤشر VVM في المرحلة C: استخدمه فوراً.")
