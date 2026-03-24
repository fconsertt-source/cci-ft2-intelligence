import csv
from typing import List

from src.domain.dtos.center_dto import CenterDTO
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def get_recommended_action(decision: str) -> str:
    """تحديد الإجراء الموصى به بناءً على القرار"""
    actions = {
        # قرارات الحرارة (النوافذ)
        "REJECTED_HEAT_SEVERE": "إتلاف جميع اللقاحات (المرحلة D: حرارة عالية أو مدة طويلة جداً)",
        "WARNING_HEAT_B": "إتلاف شلل الأطفال. استخدم الحصبة، الرباعي، الخماسي خلال 3 أشهر (المرحلة B)",
        "WARNING_EXCURSION": "مراجعة مطلوبة (تجاوز حراري تراكمي). قد يلزم إتلاف لقاحات معينة (مشابه للمرحلة C)",
        "REJECTED_HEAT_C": "إتلاف شلل الأطفال، الحصبة، الرباعي، الخماسي. استخدم الثلاثي والبي سي جي خلال 3 أشهر (المرحلة C)",
        "WARNING_HEAT_A": "استخدم شلل الأطفال خلال 3 أشهر. باقي اللقاحات طبيعي (المرحلة A)",
        # قرارات التجميد (Guard Rule) + التقييم الحراري
        "REJECTED_FREEZE_SENSITIVE": "تحقق من خاصية اللقاح: إتلاف الحساسة للتجميد فقط. الباقي سليم",
        "REJECTED_FREEZE": "رفض كامل: تجميد الطعوم (Zero Tolerance Violation)",
        "REJECTED_FREEZE_AND_HEAT_A": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال خلال 3 أشهر (مرحلة A)",
        "REJECTED_FREEZE_AND_HEAT_B": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال إتلاف، والبقية خلال 3 أشهر (مرحلة B)",
        "REJECTED_FREEZE_AND_HEAT_C": "إتلاف الحساسة للتجميد. الباقي: إتلاف معظم اللقاحات، BCG خلال 3 أشهر (مرحلة C)",
        "REJECTED_BOTH": "إتلاف كامل الشحنة (تجميد + مرحلة D حرارية)",
        "REJECTED_EXPIRED": "إتلاف فوري: اللقاح تجاوز تاريخ الصلاحية المسجل.",
        "ACCEPTED": "اللقاحات سليمة (النوافذ بيضاء). تستخدم بشكل طبيعي",
        "NO_DATA": "التحقق من سلامة الجهاز",
    }
    return actions.get(decision, f"مراجعة يدوية ({decision})")


def generate_centers_report(centers: List[CenterDTO], output_path: str):
    """إنشاء تقرير TSV للمراكز مع دعم كامل وآمن لـ JudgmentEngine"""
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out, delimiter="\t")

            writer.writerow(
                [
                    "center_id",
                    "center_name",
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
                    "judgment_risk",
                    "judgment_icon",
                    "confidence",
                    "requires_review",
                    "her_percentage",
                    "ccm_index",
                    "judgment_narrative",
                ]
            )

            for dto in centers:
                stats = getattr(dto, "stats", {}) or {}

                decision_for_action = (
                    "WARNING_EXCURSION"
                    if getattr(dto, "decision", "") == "ACCEPTED"
                    and getattr(dto, "has_warning", False)
                    else getattr(dto, "decision", "UNKNOWN")
                )
                action = get_recommended_action(decision_for_action)

                # معالجة آمنة للحقول الحرارية (قد تكون str أو None)
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default

                avg_temp = safe_float(getattr(dto, "avg_temperature", None))
                min_temp = safe_float(getattr(dto, "min_temperature", None))
                max_temp = safe_float(getattr(dto, "max_temperature", None))

                writer.writerow(
                    [
                        getattr(dto, "id", ""),
                        getattr(dto, "name", ""),
                        getattr(dto, "decision", "UNKNOWN"),
                        "YES" if getattr(dto, "has_warning", False) else "NO",
                        getattr(dto, "alert_level", "GREEN") or "GREEN",
                        getattr(dto, "vvm_stage", "NONE"),
                        f"{getattr(dto, 'stability_budget_consumed_pct', 0):.2f}",
                        (
                            f"{getattr(dto, 'thaw_remaining_hours', None):.1f}"
                            if getattr(dto, "thaw_remaining_hours", None) is not None
                            else "N/A"
                        ),
                        getattr(dto, "category_display", "General"),
                        action,
                        getattr(dto, "ft2_entries_count", 0),
                        "YES" if stats.get("has_freeze", False) else "NO",
                        "YES" if stats.get("has_ccm_violation", False) else "NO",
                        f"{avg_temp:.2f}",
                        f"{min_temp:.2f}",
                        f"{max_temp:.2f}",
                        " | ".join(getattr(dto, "decision_reasons", [])),
                        # JudgmentEngine fields
                        stats.get("judgment_risk", "SAFE"),
                        stats.get("judgment_icon", "🟢"),
                        f"{float(stats.get('confidence', 0.0)):.2f}",
                        "Yes" if stats.get("requires_review", False) else "No",
                        f"{float(stats.get('her_percentage', 0.0)):.1f}%",
                        str(stats.get("ccm_index", "")),
                        str(stats.get("judgment_narrative", ""))
                        .replace("\n", " ")
                        .strip(),
                    ]
                )

        logger.info("✅ تم إنشاء تقرير المراكز بنجاح: %s", output_path)

    except Exception as e:
        logger.error("❌ خطأ في إنشاء تقرير المراكز: %s", e)
        raise
