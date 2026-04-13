import math
import pytest
from src.domain.calculators.arrhenius_her_calculator import ArrheniusHERCalculator
from src.domain.calculators.mkt_calculator import MKTCalculator

# ─── Mock Class للتجربة السريعة بدون تعقيدات الـ Dates ───
class MockTempEntry:
    def __init__(self, temp: float, duration_mins: float):
        self.temperature = temp
        self.duration_minutes = duration_mins

class TestArrheniusHERCalculator:
    def setup_method(self):
        # Ea = 83.144 kJ/mol, Tref = 5.0 °C
        self.calc = ArrheniusHERCalculator()

    def test_baseline_temperature_gives_factor_one(self):
        """إذا كانت الحرارة تساوي تماماً الدرجة المرجعية (5°C)، فإن معدل التحلل يجب أن يكون 1.0"""
        entries = [MockTempEntry(5.0, 60.0)]  # ساعة واحدة عند 5 مئوية
        shelf_life_hours = 100.0
        
        result = self.calc.calculate(entries, shelf_life_hours)
        
        # مدة التحلل يجب أن تتطابق مع المدة الزمنية الحقيقية (1 ساعة)
        assert math.isclose(result.cumulative_degradation_hours, 1.0, rel_tol=1e-5)
        assert math.isclose(result.her_ratio, 1.0 / 100.0, rel_tol=1e-5)

    def test_higher_temperature_accelerates_degradation(self):
        """الحرارة المرتفعة (25°C) يجب أن تسرع التحلل بشكل كبير جداً مقارنة بـ 5°C"""
        entries =[MockTempEntry(25.0, 60.0)]  # ساعة واحدة عند 25 مئوية
        result = self.calc.calculate(entries, shelf_life_hours=100.0)
        
        # بناءً على Q10 ≈ 3-4، يجب أن يكون التحلل أكبر بكثير من 1.0 ساعة
        assert result.cumulative_degradation_hours > 5.0

    def test_lower_temperature_decelerates_degradation(self):
        """الحرارة المنخفضة (0°C) يجب أن تبطئ التحلل مقارنة بـ 5°C"""
        entries =[MockTempEntry(0.0, 60.0)]  # ساعة واحدة عند صفر مئوية
        result = self.calc.calculate(entries, shelf_life_hours=100.0)
        
        # التحلل يجب أن يكون أقل من 1.0 ساعة
        assert result.cumulative_degradation_hours < 1.0


class TestMKTCalculator:
    def setup_method(self):
        self.calc = MKTCalculator()

    def test_constant_temperature_mkt(self):
        """إذا كانت الحرارة ثابتة، فإن MKT يجب أن يساوي هذه الحرارة بالضبط"""
        entries =[
            MockTempEntry(5.0, 60.0),
            MockTempEntry(5.0, 60.0),
            MockTempEntry(5.0, 60.0),
        ]
        mkt = self.calc.calculate(entries)
        assert math.isclose(mkt, 5.0, rel_tol=1e-5)

    def test_mkt_is_higher_than_arithmetic_mean(self):
        """
        في حالات التذبذب الحراري، الـ MKT يعطي وزناً أسياً للحرارة المرتفعة.
        لذا يجب أن يكون أعلى من المتوسط الحسابي العادي.
        """
        entries =[
            MockTempEntry(2.0, 60.0),   # ساعة عند 2
            MockTempEntry(8.0, 60.0),   # ساعة عند 8
        ]
        
        arithmetic_mean = (2.0 + 8.0) / 2.0  # 5.0 °C
        mkt = self.calc.calculate(entries)
        
        # الكود الدقيق يحسبها 5.536
        assert mkt > arithmetic_mean
        assert math.isclose(mkt, 5.536, abs_tol=0.01)

    def test_empty_or_zero_duration_safeguards(self):
        """
        - القائمة الفارغة يجب أن تعيد 5.0.
        - القراءة ذات المدة 0 يتم تحويلها إلى دقيقة واحدة كحماية (فتعيد نفس درجة حرارتها).
        """
        assert self.calc.calculate([]) == 5.0
        
        # قراءة واحدة بحرارة 10 ومدة 0، ستعامل كدقيقة واحدة، والـ MKT لها سيكون 10
        assert self.calc.calculate([MockTempEntry(10.0, 0.0)]) == 10.0