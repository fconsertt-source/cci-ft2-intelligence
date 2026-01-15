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
        logger.error(f"❌ خطأ في إنشاء تقرير المراكز: {e}")