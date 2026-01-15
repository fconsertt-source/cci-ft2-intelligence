# analysis_result_dto.py (مُحسّن)
@dataclass
class AnalysisResultDTO:
    vaccine_id: str
    status: VaccineStatus
    her: float
    ccm: float
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
        """توليد توصيات محددة بناءً على القرار"""
        if self.status == VaccineStatus.DISCARD:
            self.recommendations = [
                "🚨 إتلاف الفورًا",
                "تسجيل سبب الإتلاف في سجلات المستودع",
                "إشعار مدير سلسلة التبريد"
            ]
        elif self.status == VaccineStatus.PARTIAL:
            self.recommendations = [
                "⚠️ استخدام خلال 3 أشهر كحد أقصى",
                "وضع علامة VVM على العبوات",
                "توزيع أولوية (استخدام أولاً)"
            ]