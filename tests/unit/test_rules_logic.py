import unittest
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any

# إضافة مسار src للعثور على الموديولات
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# استيراد المحرك الحقيقي للقواعد
from src.core.services.rules_engine import apply_rules, calculate_center_stats
from src.core.enums.vvm_stage import VVMStage

@dataclass
class MockEntry:
    temperature: float
    duration_minutes: int

class MockCenter:
    def __init__(self, id: str, name: str, temp_ranges: dict, thresholds: dict, freeze_sensitive: bool = True):
        self.id = id
        self.name = name
        self.temperature_ranges = temp_ranges
        self.decision_thresholds = thresholds
        self.freeze_sensitive = freeze_sensitive
        self.ft2_entries: List[MockEntry] = []
        self.decision = "UNKNOWN" # سيتم تحديثه بواسطة apply_rules


class TestRulesLogic(unittest.TestCase):
    """اختبارات شاملة لمنطق القواعد الديناميكي (WHO + Center Profiles)"""

    def setUp(self):
        """إعداد مركز اختبار افتراضي"""
        self.center_config = {
            'temperature_ranges': {'max': 8.0},
            'decision_thresholds': {'freeze_threshold': -0.5, 'ccm_limit': 600}
        }
        self.center = MockCenter("TEST001", "مركز الاختبار", 
                               self.center_config['temperature_ranges'],
                               self.center_config['decision_thresholds'])

    def test_freeze_zero_tolerance(self):
        """اختبار التجميد: أي مدة > 0 = REJECTED_FREEZE"""
        self.center.ft2_entries = [
            MockEntry(temperature=-1.0, duration_minutes=1),  # انتهاك تجميد
            MockEntry(temperature=5.0, duration_minutes=100)
        ]
        
        apply_rules(self.center)
        stats = calculate_center_stats(self.center)
        
        self.assertIn('REJECTED_FREEZE', self.center.decision)
        self.assertEqual(stats['freeze_duration'], 1)
        self.assertTrue(stats['has_freeze'])

    def test_freeze_resistant_vaccine(self):
        """اختبار لقاح مقاوم للتجميد: يجب أن يعطي تحذير بدلاً من رفض"""
        # مركز بلقاحات مقاومة للتجميد
        self.center.freeze_sensitive = False
        self.center.ft2_entries = [
            MockEntry(temperature=-1.0, duration_minutes=10) # تجميد
        ]
        
        apply_rules(self.center)
        
        # نتوقع تحذير لأن الحرارة < 2، ولكن ليس رفض تجميد
        self.assertEqual(self.center.decision, 'ACCEPTED')
        self.assertTrue(getattr(self.center, 'has_warning', False))

    def test_heat_cumulative_ccm(self):
        """اختبار الحرارة: تراكمي يجب > ccm_limit"""
        self.center.ft2_entries = [
            MockEntry(temperature=9.0, duration_minutes=300),  # 5 ساعات
            MockEntry(temperature=9.5, duration_minutes=400),  # 6.67 ساعات
        ]
        
        apply_rules(self.center)
        stats = calculate_center_stats(self.center)
        
        self.assertEqual(self.center.decision, 'REJECTED_HEAT_C')
        self.assertEqual(stats['heat_duration'], 700)
        self.assertTrue(stats['has_ccm_violation'])

    def test_heat_below_ccm_limit(self):
        """اختبار الحرارة: تحت الحد التراكمي = ACCEPTED"""
        self.center.ft2_entries = [
            MockEntry(temperature=9.0, duration_minutes=200),  # 3.33 ساعات < 10
        ]
        
        apply_rules(self.center)
        stats = calculate_center_stats(self.center)
        
        self.assertEqual(self.center.decision, 'ACCEPTED')
        self.assertEqual(stats['heat_duration'], 200)
        self.assertFalse(stats['has_ccm_violation'])

    def test_temperature_warning_range(self):
        """اختبار نطاق التحذير (8-10 درجات)"""
        self.center.ft2_entries = [
            MockEntry(temperature=9.0, duration_minutes=100) # > 8 ولكن < 10
        ]
        
        apply_rules(self.center)
        
        self.assertEqual(self.center.decision, 'ACCEPTED')
        self.assertTrue(getattr(self.center, 'has_warning', False))

    def test_freeze_takes_precedence(self):
        """اختبار الأولوية: التجميد يسبق الحرارة"""
        self.center.ft2_entries = [
            MockEntry(temperature=-2.0, duration_minutes=1),   # تجميد
            MockEntry(temperature=12.0, duration_minutes=1000) # حرارة شديدة
        ]
        
        apply_rules(self.center)
        
        self.assertIn('REJECTED_FREEZE', self.center.decision)
        self.assertNotEqual(self.center.decision, 'REJECTED_HEAT_C')

    def test_dynamic_thresholds(self):
        """اختبار الإعدادات الديناميكية للمركز"""
        # مركز بإعدادات مختلفة
        custom_center = MockCenter("CUSTOM001", "مركز مخصص",
                                 {'max': 6.0},  # حد أقل
                                 {'freeze_threshold': -1.0, 'ccm_limit': 300})
        custom_center.ft2_entries = [
            MockEntry(temperature=7.0, duration_minutes=400)  # > 6°C لـ 6.67 ساعات
        ]
        
        apply_rules(custom_center)
        stats = calculate_center_stats(custom_center)
        
        self.assertEqual(custom_center.decision, 'REJECTED_HEAT_C')
        self.assertTrue(stats['has_ccm_violation'])
        # تم التحقق من الحدود ضمنياً عبر النتيجة

    def test_no_violations(self):
        """اختبار عدم وجود انتهاكات"""
        self.center.ft2_entries = [
            MockEntry(temperature=4.0, duration_minutes=1440),  # طبيعي
            MockEntry(temperature=7.5, duration_minutes=100)    # قريب لكن آمن
        ]
        
        apply_rules(self.center)
        stats = calculate_center_stats(self.center)
        
        self.assertEqual(self.center.decision, 'ACCEPTED')
        self.assertEqual(stats['freeze_duration'], 0)
        self.assertFalse(stats['has_ccm_violation'])

    def test_empty_entries(self):
        """اختبار عدم وجود بيانات"""
        self.center.ft2_entries = []
        
        apply_rules(self.center)
        stats = calculate_center_stats(self.center)
        
        self.assertEqual(self.center.decision, 'NO_DATA')
        self.assertEqual(stats['freeze_duration'], 0)
        self.assertEqual(stats['heat_duration'], 0)

    def test_expiry_rule_rejection(self):
        """اختبار رفض اللقاح منتهي الصلاحية (أولوية قصوى)"""
        # تعيين تاريخ انتهاء في الماضي
        self.center.expiry_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # بيانات حرارية سليمة تماماً
        self.center.ft2_entries = [MockEntry(temperature=5.0, duration_minutes=100)]
        
        apply_rules(self.center)
        
        self.assertEqual(self.center.decision, 'REJECTED_EXPIRED')
        self.assertTrue(any("لقاح منتهي الصلاحية" in r for r in self.center.decision_reasons))

    def test_expiry_rule_valid(self):
        """اختبار قبول اللقاح ساري الصلاحية"""
        self.center.expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.center.ft2_entries = [MockEntry(temperature=5.0, duration_minutes=100)]
        
        apply_rules(self.center)
        
        self.assertEqual(self.center.decision, 'ACCEPTED')

    def test_expiry_rule_invalid_format(self):
        """اختبار التعامل الآمن مع تنسيق التاريخ الخاطئ"""
        self.center.expiry_date = "invalid-date-format"
        self.center.ft2_entries = [MockEntry(temperature=5.0, duration_minutes=100)]
        
        apply_rules(self.center)
        
        self.assertEqual(self.center.decision, 'REJECTED_EXPIRED')
        self.assertTrue(any("تنسيق تاريخ صلاحية غير صالح" in r for r in self.center.decision_reasons))

    def test_vvm_stage_rules(self):
        """اختبار قواعد مراحل VVM بناءً على قيمة HER"""
        # الحالة 1: HER = 0.5 (المرحلة B)
        self.center.ft2_entries = [MockEntry(temperature=5.0, duration_minutes=100)]
        apply_rules(self.center, extra_stats={'her': 0.5})
        self.assertEqual(self.center.vvm_stage, VVMStage.B)
        self.assertTrue(any("VVM المرحلة B" in r for r in self.center.decision_reasons))

        # الحالة 2: HER = 1.2 (المرحلة D ورفض)
        apply_rules(self.center, extra_stats={'her': 1.2, 'max_temp': 5.0})
        self.assertEqual(self.center.vvm_stage, VVMStage.D)
        self.assertEqual(self.center.decision, "REJECTED_HEAT_C")
        self.assertTrue(any("VVM المرحلة D" in r for r in self.center.decision_reasons))

        # الحالة 3: HER = 0.1 (المرحلة A)
        apply_rules(self.center, extra_stats={'her': 0.1, 'max_temp': 5.0})
        self.assertEqual(self.center.vvm_stage, VVMStage.A)
        
        # الحالة 4: HER = 0.8 (المرحلة C)
        apply_rules(self.center, extra_stats={'her': 0.8, 'max_temp': 5.0})
        self.assertEqual(self.center.vvm_stage, VVMStage.C)

    def test_heat_critical_threshold_violation(self):
        """اختبار انتهاك الحد الحراري الحرج المخصص"""
        # تعيين حد حرج 12.0 وتمرير حرارة 13.0
        self.center.ft2_entries = [MockEntry(temperature=13.0, duration_minutes=10)]
        apply_rules(self.center, extra_stats={'critical_temp_limit': 12.0, 'max_temp': 13.0})
        
        self.assertEqual(self.center.decision, "REJECTED_HEAT_C")
        self.assertTrue(any("حرارة حرجة" in r for r in self.center.decision_reasons))

if __name__ == "__main__":
    unittest.main(verbosity=2)
