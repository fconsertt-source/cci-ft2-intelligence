# src/presentation/reporting/csv_reporter.py
import csv
from typing import List

from src.application.dtos.center_dto import CenterDTO
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def get_recommended_action(decision: str) -> str:
    """تحديد الإجراء الموصى به بناءً على القرار"""
    actions = {
        "REJECTED_HEAT_SEVERE": "إتلاف جميع اللقاحات (المرحلة D: حرارة عالية أو مدة طويلة جداً)",
        "WARNING_HEAT_B": "إتلاف شلل الأطفال. استخدم الحصبة، الرباعي، الخماسي خلال 3 أشهر (المرحلة B)",
        "WARNING_EXCURSION": "مراجعة مطلوبة (تجاوز حراري تراكمي). قد يلزم إتلاف لقاحات معينة",
        "REJECTED_HEAT_C": "إتلاف شلل الأطفال، الحصبة، الرباعي، الخماسي. استخدم الثلاثي والبي سي جي خلال 3 أشهر (المرحلة C)",
        "WARNING_HEAT_A": "استخدم شلل الأطفال خلال 3 أشهر. باقي اللقاحات طبيعي (المرحلة A)",
        "REJECTED_FREEZE_SENSITIVE": "تحقق من خاصية اللقاح: إتلاف الحساسة للتجميد فقط. الباقي سليم",
        "REJECTED_FREEZE": "رفض كامل: تجميد الطعوم (Zero Tolerance Violation)",
        "REJECTED_FREEZE_AND_HEAT_A": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال خلال 3 أشهر",
        "REJECTED_FREEZE_AND_HEAT_B": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال إتلاف، والبقية خلال 3 أشهر",
        "REJECTED_FREEZE_AND_HEAT_C": "إتلاف الحساسة للتجميد. الباقي: إتلاف معظم اللقاحات، BCG خلال 3 أشهر",
        "REJECTED_BOTH": "إتلاف كامل الشحنة (تجميد + مرحلة D حرارية)",
        "REJECTED_EXPIRED": "إتلاف فوري: اللقاح تجاوز تاريخ الصلاحية المسجل.",
        "ACCEPTED": "اللقاحات سليمة (النوافذ بيضاء). تستخدم بشكل طبيعي",
        "NO_DATA": "التحقق من سلامة الجهاز",
    }
    return actions.get(decision, f"مراجعة يدوية ({decision})")


def generate_centers_report(centers: List[CenterDTO], output_path: str):
    """
    إنشاء تقرير TSV على مستوى المعدة.
    كل صف = معدة واحدة (ثلاجة / غرفة / حافظة).
    آخر صف لكل مركز = القرار المجمَّع للمركز.
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out, delimiter="\t")

            # رأس التقرير
            writer.writerow([
                "center_id",
                "center_name",
                "equipment_id",
                "equipment_name",
                "device_id",
                "decision",
                "has_warning",
                "alert_level",
                "vvm_stage",
                "stability_budget_consumed_pct",
                "thaw_remaining_hours",
                "category_display",
                "recommended_action",
                "num_ft2_entries",
                "has_freeze",
                "has_ccm_violation",
                "avg_temperature",
                "min_temperature",
                "max_temperature",
                "decision_reasons",
            ])

            for center in centers:
                # ─── صفوف المعدات ─────────────────────────────────────────
                for unit in center.equipment_units:
                    stats = unit.stats or {}
                    has_temp_stats = "avg_temp" in stats

                    decision_for_action = (
                        "WARNING_EXCURSION"
                        if unit.decision == "ACCEPTED" and unit.has_warning
                        else unit.decision
                    )

                    writer.writerow([
                        center.id,
                        center.name,
                        unit.equipment_id,
                        unit.equipment_name,
                        unit.device_id,
                        unit.decision,
                        "YES" if unit.has_warning else "NO",
                        unit.alert_level or "GREEN",
                        unit.vvm_stage,
                        f"{unit.stability_budget_consumed_pct:.2f}",
                        f"{unit.thaw_remaining_hours:.2f}" if unit.thaw_remaining_hours is not None else "N/A",
                        unit.category_display or "General",
                        get_recommended_action(decision_for_action),
                        unit.ft2_entries_count,
                        "YES" if stats.get("has_freeze", False) else "NO",
                        "YES" if stats.get("has_ccm_violation", False) else "NO",
                        f"{stats['avg_temp']:.2f}" if has_temp_stats else "N/A",
                        f"{stats['min_temp']:.2f}" if has_temp_stats else "N/A",
                        f"{stats['max_temp']:.2f}" if has_temp_stats else "N/A",
                        " | ".join(unit.decision_reasons),
                    ])

                # ─── صف تجميعي للمركز ─────────────────────────────────────
                center_decision = center.decision
                writer.writerow([
                    center.id,
                    center.name,
                    "SUMMARY",
                    f"[مجموع المركز — {len(center.equipment_units)} معدة]",
                    "—",
                    center_decision,
                    "YES" if center.has_warning else "NO",
                    center.alert_level or "GREEN",
                    center.vvm_stage,
                    f"{center.stability_budget_consumed_pct:.2f}",
                    f"{center.thaw_remaining_hours:.2f}" if center.thaw_remaining_hours is not None else "N/A",
                    center.category_display or "General",
                    get_recommended_action(center_decision),
                    center.ft2_entries_count,
                    "—", "—", "—", "—", "—",
                    " | ".join(center.decision_reasons),
                ])

        logger.info("✅ تم إنشاء تقرير المراكز: %s", output_path)

    except Exception as e:
        logger.error("❌ خطأ في إنشاء تقرير المراكز: %s", e)