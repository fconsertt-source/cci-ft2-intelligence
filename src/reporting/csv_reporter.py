import csv
from typing import List
from src.core.services.rules_engine import calculate_center_stats
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
        "NO_DATA": "التحقق من سلامة الجهاز"
    }
    return actions.get(decision, f"مراجعة يدوية ({decision})")

def generate_centers_report(centers: List, output_path: str):
    """إنشاء تقرير TSV للمراكز"""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out, delimiter='\t')
            
            # رأس التقرير المطور (v1.1.0)
            writer.writerow([
                "center_id", 
                "center_name", 
                "decision", 
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
                "decision_reasons"
            ])
            
            # بيانات كل مركز
            for center in centers:
                stats = calculate_center_stats(center)
                has_entries = bool(getattr(center, 'ft2_entries', []))
                
                decision_for_action = center.decision
                if center.decision == "ACCEPTED" and getattr(center, 'has_warning', False):
                    decision_for_action = "WARNING_EXCURSION"
                
                action = get_recommended_action(decision_for_action)
                
                # استخراج الحقول الجديدة إذا كانت متوفرة (للمستقبل)
                alert = getattr(center, 'alert_level', "GREEN")
                budget = getattr(center, 'stability_budget_consumed_pct', 0.0)
                thaw = getattr(center, 'thaw_remaining_hours', None)
                category = getattr(center, 'category_display', "General")

                writer.writerow([
                    center.id, 
                    center.name, 
                    center.decision, 
                    alert,
                    center.vvm_stage,
                    f"{budget:.2f}",
                    f"{thaw:.2f}" if thaw is not None else "N/A",
                    category,
                    action,
                    len(getattr(center, 'ft2_entries', [])), 
                    "YES" if stats['has_freeze'] else "NO", 
                    "YES" if stats['has_ccm_violation'] else "NO",
                    f"{stats['avg_temp']:.2f}" if has_entries else "N/A",
                    f"{stats['min_temp']:.2f}" if has_entries else "N/A",
                    f"{stats['max_temp']:.2f}" if has_entries else "N/A",
                    " | ".join(getattr(center, 'decision_reasons', []))
                ])
        
        logger.info(f"✅ تم إنشاء تقرير المراكز: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء تقرير المراكز: {e}")