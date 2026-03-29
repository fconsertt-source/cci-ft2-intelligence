# src/application/dtos/equipment_dto.py
# (انسخ نفس المحتوى إلى src/domain/dtos/equipment_dto.py)
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EquipmentDTO:
    """
    DTO يمثل معدة تبريد واحدة (ثلاجة / غرفة / حافظة).
    هي الوحدة الفعلية للتحليل — تحمل قراءات جهاز FT2 الخاص بها.

    العلاقة:
        CenterDTO  1 ←→ N  EquipmentDTO  1 ←→ 1  جهاز FT2
    """

    # الهوية
    equipment_id: str        # "Cold_Room" — المفتاح في YAML
    equipment_name: str      # "غرفة التبريد"
    device_id: str           # "130600112769" — رابط مع FT2
    center_id: str           # "TEST_CENTER_01" — رابط مع المركز الأب

    # إعدادات التحليل (مورَّثة من المركز)
    temperature_ranges: Dict[str, float] = field(
        default_factory=lambda: {"min": 2.0, "max": 8.0}
    )
    decision_thresholds: Dict[str, Any] = field(default_factory=dict)

    # بيانات التشغيل
    ft2_entries: List[Any] = field(default_factory=list)

    # نتائج التحليل (تُملأ بعد apply_rules / UseCase)
    decision: str = "UNKNOWN"
    vvm_stage: str = "NONE"
    alert_level: Optional[str] = None
    stability_budget_consumed_pct: float = 0.0
    thaw_remaining_hours: Optional[float] = None
    category_display: Optional[str] = None
    decision_reasons: List[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    # ─── Properties ────────────────────────────────────────────────────────────

    @property
    def ft2_entries_count(self) -> int:
        """عدد القراءات المرتبطة — محسوب تلقائياً"""
        return len(self.ft2_entries)

    @property
    def has_warning(self) -> bool:
        """هل يوجد تحذير — مشتق من alert_level أو decision"""
        if self.alert_level and self.alert_level.upper() not in ("GREEN", "NONE"):
            return True
        return self.decision in {
            "WARNING_HEAT_A",
            "WARNING_HEAT_B",
            "WARNING_EXCURSION",
            "REJECTED_FREEZE_SENSITIVE",
        }

    # ─── Interface متوافقة مع rules_engine و apply_rules ────────────────────
    # rules_engine يتوقع: center.ft2_entries, center.temperature_ranges,
    #                      center.decision_thresholds, center.decision (setter),
    #                      center.decision_reasons (list), center.vvm_stage
    # EquipmentDTO يوفر كل هذه الحقول مباشرة ← لا حاجة لأي تعديل في rules_engine

    def add_ft2_entry(self, entry: Any) -> None:
        """واجهة الربط — متوافقة مع FT2Linker.LinkableCenter Protocol"""
        self.ft2_entries.append(entry)