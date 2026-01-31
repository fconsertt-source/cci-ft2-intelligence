<<<<<<< HEAD
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
=======
import csv
import logging
from typing import List

logger = logging.getLogger(__name__)

def get_recommended_action(decision: str) -> str:
    """تحديد الإجراء الموصى به بناءً على القرار"""
    actions = {
        # قرارات الحرارة (النوافذ)
        "REJECTED_HEAT_SEVERE": "إتلاف جميع اللقاحات (المرحلة D: حرارة عالية أو مدة طويلة جداً)",
        "REJECTED_HEAT_C": "إتلاف شلل الأطفال، الحصبة، الرباعي، الخماسي. استخدم الثلاثي والبي سي جي خلال 3 أشهر (المرحلة C)",
        "WARNING_HEAT_B": "إتلاف شلل الأطفال. استخدم الحصبة، الرباعي، الخماسي خلال 3 أشهر (المرحلة B)",
        "WARNING_HEAT_A": "استخدم شلل الأطفال خلال 3 أشهر. باقي اللقاحات طبيعي (المرحلة A)",
        
        # قرارات التجميد (Guard Rule) + التقييم الحراري
        "REJECTED_FREEZE_SENSITIVE": "تحقق من خاصية اللقاح: إتلاف الحساسة للتجميد فقط. الباقي سليم",
        "REJECTED_FREEZE_AND_HEAT_A": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال خلال 3 أشهر (مرحلة A)",
        "REJECTED_FREEZE_AND_HEAT_B": "إتلاف الحساسة للتجميد. الباقي: شلل الأطفال إتلاف، والبقية خلال 3 أشهر (مرحلة B)",
        "REJECTED_FREEZE_AND_HEAT_C": "إتلاف الحساسة للتجميد. الباقي: إتلاف معظم اللقاحات، BCG خلال 3 أشهر (مرحلة C)",
        
        "REJECTED_BOTH": "إتلاف كامل الشحنة (تجميد + مرحلة D حرارية)",
        
        "ACCEPTED": "اللقاحات سليمة (النوافذ بيضاء). تستخدم بشكل طبيعي",
        "NO_DATA": "التحقق من سلامة الجهاز"
    }
    return actions.get(decision, f"مراجعة يدوية ({decision})")

def generate_centers_report(centers: List, output_path: str):
    """إنشاء تقرير TSV للمراكز"""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out, delimiter='\t')
            
            # رأس التقرير
            writer.writerow([
                "center_id", 
                "center_name", 
                "decision", 
                "vvm_stage",
                "recommended_action",
                "num_ft2_entries",
                "has_freeze",
                "has_ccm_violation",
                "freeze_duration_mins",
                "heat_duration_mins",
                "avg_temperature",
                "min_temperature",
                "max_temperature"
            ])
            
            # بيانات كل مركز
            for center in centers:
                if center.ft2_entries:
                    temperatures = [e.temperature for e in center.ft2_entries if e.temperature is not None]
                    has_freeze = any(t < -0.5 for t in temperatures) if temperatures else False
                    has_ccm = any(t > 8.0 for t in temperatures) if temperatures else False
                    
                    # حساب المدة الزمنية
                    freeze_duration = sum(e.duration_minutes for e in center.ft2_entries if e.temperature < -0.5)
                    heat_duration = sum(e.duration_minutes for e in center.ft2_entries if e.temperature > 8.0)
                    
                    avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
                    min_temp = min(temperatures) if temperatures else 0
                    max_temp = max(temperatures) if temperatures else 0
                else:
                    has_freeze = False
                    has_ccm = False
                    avg_temp = 0
                    min_temp = 0
                    max_temp = 0
                    freeze_duration = 0
                    heat_duration = 0
                
                action = get_recommended_action(center.decision)
                writer.writerow([
                    center.id, center.name, center.decision, center.vvm_stage, action,
                    len(center.ft2_entries), "YES" if has_freeze else "NO", "YES" if has_ccm else "NO",
                    int(freeze_duration), int(heat_duration),
                    f"{avg_temp:.2f}" if center.ft2_entries else "N/A",
                    f"{min_temp:.2f}" if center.ft2_entries else "N/A",
                    f"{max_temp:.2f}" if center.ft2_entries else "N/A"
                ])
        
        logger.info(f"✅ تم إنشاء تقرير المراكز: {output_path}")
        
    except Exception as e:
>>>>>>> a401e3c103f41075e342c0dfd67bb255c2193010
        logger.error(f"❌ خطأ في إنشاء تقرير المراكز: {e}")