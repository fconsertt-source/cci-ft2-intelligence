import csv
from typing import List
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def get_recommended_action(decision: str) -> str:
    actions = {
        "REJECTED_HEAT_SEVERE": "إتلاف جميع اللقاحات (المرحلة D)",
        "WARNING_HEAT_B": "إتلاف شلل الأطفال. استخدم الباقي خلال 3 أشهر (المرحلة B)",
        "WARNING_EXCURSION": "مراجعة مطلوبة (تجاوز حراري تراكمي)",
        "REJECTED_HEAT_C": "إتلاف شلل الأطفال، الحصبة، الرباعي، الخماسي (المرحلة C)",
        "WARNING_HEAT_A": "استخدم شلل الأطفال خلال 3 أشهر (المرحلة A)",
        "REJECTED_FREEZE_SENSITIVE": "إتلاف الحساسة للتجميد فقط",
        "REJECTED_FREEZE": "رفض كامل: تجميد الطعوم",
        "REJECTED_BOTH": "إتلاف كامل الشحنة",
        "REJECTED_EXPIRED": "إتلاف فوري: انتهاء الصلاحية",
        "ACCEPTED": "اللقاحات سليمة. تستخدم بشكل طبيعي",
        "NO_DATA": "التحقق من سلامة الجهاز",
    }
    return actions.get(decision, f"مراجعة يدوية ({decision})")


def generate_centers_report(centers, output_path: str):
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out, delimiter="\t")
            writer.writerow([
                "center_id", "center_name", "equipment_id", "equipment_name", "device_id",
                "decision", "has_warning", "alert_level", "vvm_stage",
                "stability_budget_consumed_pct", "thaw_remaining_hours",
                "category_display", "recommended_action", "num_ft2_entries",
                "has_freeze", "has_ccm_violation", "avg_temperature",
                "min_temperature", "max_temperature", "decision_reasons",
            ])

            for center in centers:
                # كتابة صف لكل معدة (equipment unit)
                for unit in getattr(center, 'equipment_units', []):
                    stats = getattr(unit, 'stats', {}) or {}
                    ft2_entries = getattr(unit, 'ft2_entries', [])
                    has_entries = len(ft2_entries) > 0
                    decision = getattr(unit, 'decision', 'UNKNOWN')
                    has_warning = getattr(unit, 'has_warning', False)
                    decision_for_action = "WARNING_EXCURSION" if decision == "ACCEPTED" and has_warning else decision

                    writer.writerow([
                        getattr(center, 'id', ''),
                        getattr(center, 'name', ''),
                        getattr(unit, 'equipment_id', ''),
                        getattr(unit, 'equipment_name', ''),
                        getattr(unit, 'device_id', ''),
                        decision,
                        "YES" if has_warning else "NO",
                        getattr(unit, 'alert_level', None) or "GREEN",
                        str(getattr(unit, 'vvm_stage', 'NONE')).replace('VVMStage.', ''),
                        f"{getattr(unit, 'stability_budget_consumed_pct', 0.0):.2f}",
                        f"{getattr(unit, 'thaw_remaining_hours', None):.2f}" if getattr(unit, 'thaw_remaining_hours', None) is not None else "N/A",
                        getattr(unit, 'category_display', None) or "General",
                        get_recommended_action(decision_for_action),
                        len(ft2_entries),
                        "YES" if stats.get("has_freeze", False) else "NO",
                        "YES" if stats.get("has_ccm_violation", False) else "NO",
                        f"{stats.get('avg_temperature', 0):.2f}" if has_entries else "N/A",
                        f"{stats.get('min_temperature', 0):.2f}" if has_entries else "N/A",
                        f"{stats.get('max_temperature', 0):.2f}" if has_entries else "N/A",
                        " | ".join(getattr(unit, 'decision_reasons', [])),
                    ])

                # صف تلخيصي للمركز (اختياري)
                total_entries = sum(len(getattr(u, 'ft2_entries', [])) for u in getattr(center, 'equipment_units', []))
                writer.writerow([
                    getattr(center, 'id', ''),
                    getattr(center, 'name', ''),
                    "SUMMARY",
                    f"[مجموع المركز — {len(getattr(center, 'equipment_units', []))} معدة]",
                    "—",
                    "UNKNOWN", "NO", "GREEN", "", "0.00", "N/A", "General",
                    "مراجعة يدوية (UNKNOWN)", total_entries, "—", "—", "—", "—", "—", ""
                ])

        logger.info("✅ تم إنشاء تقرير المراكز: %s", output_path)
    except Exception as e:
        logger.error("❌ خطأ في إنشاء تقرير المراكز: %s", e)