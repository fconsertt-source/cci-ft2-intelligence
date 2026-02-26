import csv
from typing import List
from src.application.dtos.center_dto import CenterDTO
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

def generate_centers_report(centers: List[CenterDTO], output_path: str):
    """إنشاء تقرير TSV للمراكز اعتماداً على CenterDTO"""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out, delimiter='\t')
            
            # رأس التقرير المطور (v2.0.0)
            writer.writerow([
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
                "decision_reasons"
            ])
            
            # بيانات كل مركز
            for dto in centers:
                stats = dto.stats
                has_entries = dto.ft2_entries_count > 0
                
                # استخدم الحقل الرسمي has_warning
                decision_for_action = "WARNING_EXCURSION" if dto.decision == "ACCEPTED" and dto.has_warning else dto.decision
                
                action = get_recommended_action(decision_for_action)
                
                writer.writerow([
                    dto.id, 
                    dto.name, 
                    dto.decision, 
                    "YES" if dto.has_warning else "NO",
                    dto.alert_level or "GREEN",
                    dto.vvm_stage,
                    f"{dto.stability_budget_consumed_pct:.2f}",
                    f"{dto.thaw_remaining_hours:.2f}" if dto.thaw_remaining_hours is not None else "N/A",
                    dto.category_display or "General",
                    action,
                    dto.ft2_entries_count,
                    "YES" if stats.get('has_freeze', False) else "NO",
                    "YES" if stats.get('has_ccm_violation', False) else "NO",
                    f"{stats['avg_temp']:.2f}" if has_entries else "N/A",
                    f"{stats['min_temp']:.2f}" if has_entries else "N/A",
                    f"{stats['max_temp']:.2f}" if has_entries else "N/A",
                    " | ".join(dto.decision_reasons)
                ])
        
        logger.info(f"✅ تم إنشاء تقرير المراكز: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء تقرير المراكز: {e}")
