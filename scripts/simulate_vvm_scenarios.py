import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List

# إضافة المسار الجذري للمشروع للوصول إلى الكود المصدري
sys.path.append(str(Path(__file__).parent.parent))

from src.core.entities.vaccination_center import VaccinationCenter

@dataclass
class MockEntry:
    """محاكاة إدخال FT2 (درجة حرارة ومدة)"""
    temperature: float
    duration_minutes: float

def simulate_scenario(name: str, entries: List[MockEntry]):
    """تشغيل سيناريو واحد وطباعة النتيجة في صف الجدول"""
    
    # إعداد مركز افتراضي للمحاكاة
    center = VaccinationCenter(
        id="SIM",
        name="Simulation",
        device_ids=["SIM001"],
        temperature_ranges={"min": 2, "max": 8},
        decision_thresholds={}
    )
    
    # إضافة الإدخالات للمركز
    for entry in entries:
        center.add_ft2_entry(entry)
    
    # حساب إجمالي المدة فوق 8 درجات (لغرض العرض في الجدول فقط)
    total_heat_duration = sum(e.duration_minutes for e in entries if e.temperature > 8.0)
    days = total_heat_duration / (24 * 60)
    
    # تنسيق وصف المدخلات
    input_desc = " + ".join([f"{e.temperature}°C({e.duration_minutes/60:.1f}h)" for e in entries])
    if len(input_desc) > 45: input_desc = input_desc[:42] + "..."
    
    # طباعة الصف
    # الأعمدة: السيناريو | المدخلات | التراكم (>8°C) | المرحلة | القرار النهائي
    print(f"| {name:<25} | {input_desc:<45} | {days:<6.1f} days | {center.vvm_stage:<5} | {center.decision:<30} |")

def main():
    print("\n=== محاكاة سيناريوهات VVM (نظام النوافذ والقرارات) ===")
    print("=" * 129)
    print(f"| {'Scenario':<25} | {'Input (Temp & Duration)':<45} | {'Cumul.':<11} | {'Stage':<5} | {'Decision':<30} |")
    print("=" * 129)
    
    # 1. الوضع المثالي
    simulate_scenario("1. Ideal Condition", [
        MockEntry(5.0, 30 * 24 * 60) # 30 يوم درجة 5 (سليم)
    ])
    
    # 2. تعرض بسيط (أقل من يومين) -> لا يوجد مرحلة
    simulate_scenario("2. Minor Heat", [
        MockEntry(9.0, 1.5 * 24 * 60) # 1.5 يوم درجة 9
    ])
    
    # 3. المرحلة A (بين 2 و 6 أيام)
    simulate_scenario("3. Stage A", [
        MockEntry(15.0, 3 * 24 * 60) # 3 أيام درجة 15
    ])
    
    # 4. المرحلة B (بين 6 و 11 يوم)
    simulate_scenario("4. Stage B", [
        MockEntry(20.0, 7 * 24 * 60) # 7 أيام درجة 20
    ])
    
    # 5. المرحلة C (بين 11 و 14 يوم)
    simulate_scenario("5. Stage C", [
        MockEntry(12.0, 12 * 24 * 60) # 12 يوم درجة 12
    ])
    
    # 6. المرحلة D (تراكمي > 14 يوم) - حالتك المحددة
    simulate_scenario("6. Stage D (Cumulative)", [
        MockEntry(16.0, 21 * 24 * 60) # 21 يوم درجة 16
    ])
    
    # 7. المرحلة D (حرارة شديدة >= 34 لمدة ساعتين)
    simulate_scenario("7. Stage D (Severe)", [
        MockEntry(35.0, 120) # ساعتين (120 دقيقة) درجة 35
    ])
    
    # 8. تجميد فقط (Guard Rule)
    simulate_scenario("8. Freeze (Guard Rule)", [
        MockEntry(-5.0, 60) # ساعة تجميد
    ])
    
    # 9. تجميد + مرحلة B (شرط حاكم مشروط)
    simulate_scenario("9. Freeze + Stage B", [
        MockEntry(-2.0, 60),         # تجميد
        MockEntry(15.0, 7 * 24 * 60) # 7 أيام حرارة
    ])

    # 10. تجميد + مرحلة D (تلف كلي)
    simulate_scenario("10. Freeze + Stage D", [
        MockEntry(-2.0, 60),          # تجميد
        MockEntry(16.0, 21 * 24 * 60) # 21 يوم حرارة
    ])
    
    # 11. تجميد + حرارة آمنة (إثبات فصل CCM عن التجميد)
    # حرارة 9 درجات لمدة يوم واحد (لا تكفي للمرحلة A) + تجميد
    simulate_scenario("11. Freeze + Safe Heat", [
        MockEntry(-2.0, 60),          # تجميد
        MockEntry(9.0, 24 * 60)       # يوم واحد حرارة (>8°C)
    ])
    
    print("-" * 129)

if __name__ == "__main__":
    main()