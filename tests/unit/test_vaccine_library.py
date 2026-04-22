#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار وحدة لنظام مراقبة اللقاحات الحرارية - CCI-FT2 v2.1.0
يختبر: تحميل المكتبة، المعادلات الحرارية، حدود القرار، وخصوصيات فايزر
"""

import pytest
import yaml
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ============================================================
# الثوابت الفيزيائية والكيميائية
# ============================================================
R = 8.314  # J/mol·K - ثابت الغازات
DEFAULT_EA = 83.144  # kJ/mol - طاقة التنشيط للقاحات الحساسة
DEFAULT_Q10 = 2.0  # للقاحات التقليدية
MRNA_Q10 = 4.0  # للقاحات الرنا المرسال
SAFETY_MARGIN = 0.85  # عامل الأمان 15%

# ============================================================
# دوال الحسابات الحرارية الأساسية
# ============================================================

def celsius_to_kelvin(celsius: float) -> float:
    """تحويل درجة الحرارة من مئوية إلى كلفن"""
    return celsius + 273.15

def calculate_mkt_arrhenius(
    temperatures_c: List[float], 
    time_intervals_min: List[float],
    ea_kj_mol: float = DEFAULT_EA,
    r: float = R
) -> float:
    """
    حساب متوسط درجة الحرارة الحركي (MKT) باستخدام نموذج أرينيوس
    
    MKT = (Ea/R) / [-ln( Σ(exp(-Ea/(R×T_K)) × Δt) / ΣΔt )] - 273.15
    """
    ea_j_mol = ea_kj_mol * 1000  # تحويل kJ إلى J
    total_time = sum(time_intervals_min)
    
    if total_time == 0:
        raise ValueError("إجمالي الوقت لا يمكن أن يكون صفرًا")
    
    weighted_sum = sum(
        math.exp(-ea_j_mol / (r * celsius_to_kelvin(t))) * dt
        for t, dt in zip(temperatures_c, time_intervals_min)
    )
    
    avg_exp = weighted_sum / total_time
    mkt_k = (ea_j_mol / r) / (-math.log(avg_exp))
    
    return mkt_k - 273.15  # العودة إلى درجة مئوية

def calculate_her_q10(
    temperature_profiles: List[Dict[str, float]],
    shelf_life_hours: float,
    q10: float = DEFAULT_Q10,
    t_ref: float = 5.0
) -> float:
    """
    حساب نسبة التعرض الحراري (HER) باستخدام نموذج Q10
    
    HER = Σ[ Q10^((T-Tref)/10) × Δt_hours ] / shelf_life_hours
    """
    accumulated_exposure = 0
    
    for profile in temperature_profiles:
        t = profile['temp_c']
        dt_hours = profile['duration_hours']
        acceleration = q10 ** ((t - t_ref) / 10)
        accumulated_exposure += acceleration * dt_hours
    
    return accumulated_exposure / shelf_life_hours

def calculate_hei_linear(
    temperature_profiles: List[Dict[str, float]],
    threshold_c: float = 8.0
) -> float:
    """
    حساب مؤشر التعرض الحراري (HEI) - النموذج الخطي
    
    HEI = Σ[ max(0, T_avg - threshold) × Δt_minutes ]
    """
    hei = 0
    for profile in temperature_profiles:
        t = profile['temp_c']
        dt_min = profile['duration_minutes']
        if t > threshold_c:
            hei += (t - threshold_c) * dt_min
    return hei

def calculate_ccm(
    temperature_profiles: List[Dict[str, float]],
    t_min: float = -90.0
) -> float:
    """
    حساب الدقائق الباردة التراكمية (CCM) - نظري فقط
    
    CCM = Σ[ max(0, T_min - T) × Δt_minutes ] لـ T < T_min
    """
    ccm = 0
    for profile in temperature_profiles:
        t = profile['temp_c']
        dt_min = profile['duration_minutes']
        if t < t_min:
            ccm += (t_min - t) * dt_min
    return ccm

def apply_safety_margin(value: float, margin: float = SAFETY_MARGIN) -> float:
    """تطبيق عامل الأمان 15% على القيم الحدية"""
    return value * margin

# ============================================================
# فئة تحميل والتحقق من مكتبة اللقاحات
# ============================================================

class VaccineLibrary:
    """فئة لإدارة تحميل والتحقق من ملف vaccine_library.yaml"""
    
    def __init__(self, yaml_path: str):
        self.yaml_path = Path(yaml_path)
        self.data = None
        self._load()
    
    def _load(self):
        """تحميل ملف YAML والتحقق من صحته"""
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {self.yaml_path}")
        
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)
        
        self._validate_structure()
    
    def _validate_structure(self):
        """التحقق من الهيكل الأساسي للملف"""
        assert 'metadata' in self.data, "مفقود: metadata"
        assert 'defaults' in self.data, "مفقود: defaults"
        assert 'vaccines' in self.data, "مفقود: vaccines"
        assert 'changelog' in self.data, "مفقود: changelog"
        
        # التحقق من إصدار المخطط
        assert self.data['metadata']['schema_version'] == "2.0"
    
    def get_vaccine(self, code: str) -> Optional[Dict]:
        """الحصول على بيانات لقاح محدد"""
        return self.data['vaccines'].get(code)
    
    def get_defaults(self) -> Dict:
        """الحصول على القيم الافتراضية"""
        return self.data['defaults']
    
    def validate_pfizer_storage_phases(self) -> bool:
        """التحقق من صحة مراحل تخزين فايزر"""
        pfizer = self.get_vaccine('COVID_PFIZER')
        if not pfizer or 'storage_phases' not in pfizer:
            return False
        
        phases = pfizer['storage_phases']
        required_phases = ['ultra_low_temp', 'thawed_refrigerated', 
                          'room_temp_before_dilution', 'after_dilution']
        
        return all(phase in phases for phase in required_phases)

# ============================================================
# فئة تقييم قرار الاستخدام
# ============================================================

class DecisionEngine:
    """محرك اتخاذ القرار بناءً على مؤشرات المراقبة الحرارية"""
    
    def __init__(self, vaccine_config: Dict, defaults: Dict):
        self.config = vaccine_config
        self.defaults = defaults
        self.safety_margin = defaults.get('limits', {}).get('safety_margin_factor', SAFETY_MARGIN)
    
    def evaluate_her(self, her_value: float) -> str:
        """تقييم قيمة HER وإرجاع القرار"""
        operational_limit = apply_safety_margin(
            self.config.get('monitoring_limits', {}).get('her_limit_theoretical', 0.85),
            self.safety_margin
        )
        
        if her_value < operational_limit:
            return "✅ مقبول"
        elif her_value <= self.config.get('monitoring_limits', {}).get('her_limit_theoretical', 0.85):
            return "⚠️ مراجعة"
        else:
            return "❌ مرفوض"
    
    def evaluate_mkt(self, mkt_value: float) -> str:
        """تقييم قيمة MKT وإرجاع القرار"""
        limit = self.config.get('monitoring_limits', {}).get('mkt_limit_c', 8.0)
        
        if mkt_value <= limit:
            return "✅ مقبول"
        elif mkt_value <= limit + 4:  # هامش مراجعة 4 درجات
            return "⚠️ مراجعة"
        else:
            return "❌ مرفوض"
    
    def evaluate_hei(self, hei_value: float) -> str:
        """تقييم قيمة HEI وإرجاع القرار"""
        limit = self.config.get('monitoring_limits', {}).get('heat_exposure_index_deg_min', 3000)
        operational_limit = apply_safety_margin(limit, self.safety_margin)
        
        if hei_value <= operational_limit:
            return "✅ مقبول"
        elif hei_value <= limit:
            return "⚠️ مراجعة"
        else:
            return "❌ مرفوض"

# ============================================================
# اختبارات الوحدة باستخدام pytest
# ============================================================

class TestVaccineLibraryLoading:
    """اختبارات تحميل مكتبة اللقاحات"""
    
    @pytest.fixture
    def library(self):
        return VaccineLibrary('config/vaccine_library.yaml')
    
    def test_file_exists(self, library):
        """التحقق من وجود الملف وتحميله بنجاح"""
        assert library.data is not None
    
    def test_metadata_structure(self, library):
        """التحقق من هيكل البيانات الوصفية"""
        metadata = library.data['metadata']
        assert metadata['schema_version'] == "2.0"
        assert metadata['document_version'] == "2.0.3"
        assert metadata['review_status'] == "approved"
    
    def test_defaults_values(self, library):
        """التحقق من القيم الافتراضية"""
        defaults = library.get_defaults()
        assert defaults['reference_temp_c'] == 5.0
        assert defaults['critical_temp_c'] == 34.0
        assert defaults['ccm_default_limit'] == 600
    
    def test_pfizer_exists(self, library):
        """التحقق من وجود لقاح فايزر في المكتبة"""
        pfizer = library.get_vaccine('COVID_PFIZER')
        assert pfizer is not None
        assert pfizer['name_ar'] == "كوفيد-19 فايزر (Comirnaty)"
    
    def test_pfizer_q10_factor(self, library):
        """التحقق من عامل Q10 لفايزر (يجب أن يكون 4.0 للرنا المرسال)"""
        pfizer = library.get_vaccine('COVID_PFIZER')
        assert pfizer['q10_factor'] == 4.0, "يجب أن يكون Q10=4.0 للقاحات mRNA"
    
    def test_pfizer_storage_phases(self, library):
        """التحقق من وجود مراحل التخزين الأربعة لفايزر"""
        assert library.validate_pfizer_storage_phases() == True
    
    def test_pfizer_dosing_by_cap_color(self, library):
        """التحقق من تحديد الجرعات حسب لون الغطاء"""
        pfizer = library.get_vaccine('COVID_PFIZER')
        dosing = pfizer['dosing_by_cap_color']
        
        # التحقق من العروض الأربعة
        assert 'maroon' in dosing  # 6 أشهر - 4 سنوات
        assert 'orange' in dosing   # 5-11 سنة
        assert 'purple' in dosing   # 12+ سنة (يحتاج تخفيف)
        assert 'gray' in dosing     # 12+ سنة (جاهز للاستخدام)
        
        # التحقق من أن العرض البرتقالي يحتاج تخفيف
        assert dosing['orange']['dilution_required'] == True
        # التحقق من أن العرض الرمادي لا يحتاج تخفيف
        assert dosing['gray']['dilution_required'] == False

class TestThermalCalculations:
    """اختبارات المعادلات الحرارية"""
    
    def test_celsius_to_kelvin(self):
        """اختبار تحويل درجات الحرارة"""
        assert celsius_to_kelvin(0) == 273.15
        assert celsius_to_kelvin(5) == 278.15
        assert celsius_to_kelvin(-90) == 183.15
    
    def test_mkt_constant_temperature(self):
        """اختبار MKT لدرجة حرارة ثابتة (يجب أن يعيد نفس القيمة)"""
        temps = [5.0] * 10
        intervals = [60] * 10  # 10 فترات × 60 دقيقة = 10 ساعات
        
        mkt = calculate_mkt_arrhenius(temps, intervals)
        assert abs(mkt - 5.0) < 0.01, f"MKT لدرجة ثابتة 5°م يجب أن يكون ≈5، لكن حصلنا على {mkt}"
    
    def test_mkt_higher_temperature_increases_mkt(self):
        """اختبار أن ارتفاع درجة الحرارة يرفع قيمة MKT"""
        # حالة أساسية: جميع القراءات 5°م
        base_temps = [5.0] * 10
        intervals = [60] * 10
        base_mkt = calculate_mkt_arrhenius(base_temps, intervals)
        
        # حالة مع انحراف: 8 فترات عند 5°م + فترتان عند 15°م
        elevated_temps = [5.0] * 8 + [15.0] * 2
        elevated_mkt = calculate_mkt_arrhenius(elevated_temps, intervals)
        
        assert elevated_mkt > base_mkt, "MKT يجب أن يرتفع مع ارتفاع درجات الحرارة"
        assert 5.0 < elevated_mkt < 15.0, f"MKT يجب أن يكون بين 5 و15، لكن حصلنا على {elevated_mkt}"
    
    def test_her_q10_at_reference_temperature(self):
        """اختبار HER عند درجة المرجع (يجب أن يعيد الوقت الفعلي/العمر الافتراضي)"""
        profiles = [{'temp_c': 5.0, 'duration_hours': 168}]  # أسبوع واحد عند 5°م
        shelf_life = 1680  # 10 أسابيع بالساعات
        
        her = calculate_her_q10(profiles, shelf_life, q10=4.0, t_ref=5.0)
        expected = 168 / 1680  # 0.1
        
        assert abs(her - expected) < 0.001, f"HER المتوقع {expected}، لكن حصلنا على {her}"
    
    def test_her_q10_acceleration_at_higher_temp(self):
        """اختبار تسارع HER عند درجات حرارة أعلى مع Q10=4.0"""
        # ساعة واحدة عند 15°م مع Q10=4.0 و Tref=5°م
        # عامل التسارع = 4^((15-5)/10) = 4^1 = 4
        profiles = [{'temp_c': 15.0, 'duration_hours': 1}]
        shelf_life = 1680
        
        her = calculate_her_q10(profiles, shelf_life, q10=4.0, t_ref=5.0)
        expected = (4.0 * 1) / 1680  # 0.00238...
        
        assert abs(her - expected) < 0.0001, f"HER المتوقع {expected}، لكن حصلنا على {her}"
    
    def test_hei_below_threshold_returns_zero(self):
        """اختبار HEI عندما تكون جميع الدرجات تحت العتبة"""
        profiles = [
            {'temp_c': 5.0, 'duration_minutes': 60},
            {'temp_c': 7.9, 'duration_minutes': 60}
        ]
        
        hei = calculate_hei_linear(profiles, threshold_c=8.0)
        assert hei == 0, "HEI يجب أن يكون 0 عندما تكون جميع الدرجات ≤ 8°م"
    
    def test_hei_above_threshold_calculation(self):
        """اختبار حساب HEI عندما تتجاوز الدرجات العتبة"""
        # ساعتان عند 12°م مع عتبة 8°م
        # HEI = (12-8) × 120 دقيقة = 4 × 120 = 480
        profiles = [{'temp_c': 12.0, 'duration_minutes': 120}]
        
        hei = calculate_hei_linear(profiles, threshold_c=8.0)
        assert hei == 480, f"HEI المتوقع 480، لكن حصلنا على {hei}"
    
    def test_ccm_below_threshold_returns_zero(self):
        """اختبار CCM عندما تكون جميع الدرجات فوق T_min"""
        profiles = [
            {'temp_c': -80.0, 'duration_minutes': 60},
            {'temp_c': -60.0, 'duration_minutes': 60}
        ]
        
        ccm = calculate_ccm(profiles, t_min=-90.0)
        assert ccm == 0, "CCM يجب أن يكون 0 عندما تكون جميع الدرجات ≥ -90°م"

class TestPfizerSpecificScenarios:
    """اختبارات سيناريوهات خاصة بلقاح فايزر-بيونتيك"""
    
    @pytest.fixture
    def pfizer_config(self):
        library = VaccineLibrary('config/vaccine_library.yaml')
        return library.get_vaccine('COVID_PFIZER'), library.get_defaults()
    
    def test_pfizer_ult_storage_validation(self, pfizer_config):
        """التحقق من صحة إعدادات التخزين فائق البرودة لفايزر"""
        config, defaults = pfizer_config
        ult = config['storage_phases']['ultra_low_temp']
        
        assert ult['temp_range_c'] == [-90, -60]
        assert ult['shelf_life_months'] == 18
        assert ult['transport_allowed'] == True
    
    def test_pfizer_thawed_storage_validation(self, pfizer_config):
        """التحقق من صحة إعدادات التخزين المبرد بعد الذوبان"""
        config, defaults = pfizer_config
        ref = config['storage_phases']['thawed_refrigerated']
        
        assert ref['temp_range_c'] == [2, 8]
        assert ref['shelf_life_weeks'] == 10
        assert ref['shelf_life_hours'] == 1680
    
    def test_pfizer_dilution_window(self, pfizer_config):
        """التحقق من مهلة الاستخدام بعد التخفيف"""
        config, defaults = pfizer_config
        post_dil = config['storage_phases']['after_dilution']
        
        assert post_dil['temp_range_c'] == [2, 25]
        assert post_dil['max_hours'] == 12
    
    def test_pfizer_dosing_maroon_cap(self, pfizer_config):
        """التحقق من جرعات الغطاء العنابي (6 أشهر - 4 سنوات)"""
        config, defaults = pfizer_config
        dosing = config['dosing_by_cap_color']['maroon']
        
        assert dosing['age_range'] == "6m-4y"
        assert dosing['dose_mcg'] == 3
        assert dosing['dilution_required'] == True
        assert dosing['diluent_ml'] == 1.3
        assert dosing['dose_volume_ml'] == 0.2
    
    def test_pfizer_dosing_orange_cap(self, pfizer_config):
        """التحقق من جرعات الغطاء البرتقالي (5-11 سنة)"""
        config, defaults = pfizer_config
        dosing = config['dosing_by_cap_color']['orange']
        
        assert dosing['age_range'] == "5y-11y"
        assert dosing['dose_mcg'] == 10
        assert dosing['dilution_required'] == True
        assert dosing['doses_per_vial'] == 10
    
    def test_pfizer_gray_cap_no_dilution(self, pfizer_config):
        """التحقق من أن الغطاء الرمادي لا يحتاج تخفيف"""
        config, defaults = pfizer_config
        dosing = config['dosing_by_cap_color']['gray']
        
        assert dosing['dilution_required'] == False
        assert dosing['diluent_ml'] == 0
        assert dosing['doses_per_vial'] == 1

class TestDecisionEngine:
    """اختبارات محرك اتخاذ القرار"""
    
    @pytest.fixture
    def decision_engine(self):
        library = VaccineLibrary('config/vaccine_library.yaml')
        pfizer = library.get_vaccine('COVID_PFIZER')
        defaults = library.get_defaults()
        return DecisionEngine(pfizer, defaults)
    
    def test_her_acceptable_below_operational_limit(self, decision_engine):
        """HER تحت الحد التشغيلي (مع عامل الأمان) = مقبول"""
        # الحد النظري 0.85 × عامل الأمان 0.85 = 0.7225
        assert decision_engine.evaluate_her(0.70) == "✅ مقبول"
    
    def test_her_review_zone(self, decision_engine):
        """HER بين الحد التشغيلي والنظري = مراجعة"""
        assert decision_engine.evaluate_her(0.80) == "⚠️ مراجعة"
    
    def test_her_rejected_above_theoretical_limit(self, decision_engine):
        """HER فوق الحد النظري = مرفوض"""
        assert decision_engine.evaluate_her(0.90) == "❌ مرفوض"
    
    def test_mkt_acceptable_within_limit(self, decision_engine):
        """MKT ≤ 8°م = مقبول"""
        assert decision_engine.evaluate_mkt(5.0) == "✅ مقبول"
        assert decision_engine.evaluate_mkt(8.0) == "✅ مقبول"
    
    def test_mkt_review_zone(self, decision_engine):
        """MKT بين 8-12°م = مراجعة"""
        assert decision_engine.evaluate_mkt(10.0) == "⚠️ مراجعة"
    
    def test_mkt_rejected_above_limit(self, decision_engine):
        """MKT > 12°م = مرفوض"""
        assert decision_engine.evaluate_mkt(15.0) == "❌ مرفوض"
    
    def test_hei_acceptable_with_safety_margin(self, decision_engine):
        """HEI تحت الحد التشغيلي = مقبول"""
        # الحد 3000 × 0.85 = 2550
        assert decision_engine.evaluate_hei(2500) == "✅ مقبول"
    
    def test_hei_rejected_above_limit(self, decision_engine):
        """HEI فوق 3000 = مرفوض"""
        assert decision_engine.evaluate_hei(3500) == "❌ مرفوض"

class TestSafetyMarginApplication:
    """اختبارات تطبيق عامل الأمان"""
    
    def test_safety_margin_reduces_limit(self):
        """عامل الأمان يقلل الحدود التشغيلية"""
        theoretical = 0.85
        operational = apply_safety_margin(theoretical)
        assert operational == 0.85 * 0.85  # ≈ 0.7225
        assert operational < theoretical
    
    def test_safety_margin_on_hei_limit(self):
        """تطبيق عامل الأمان على حد HEI"""
        limit = 3000
        operational = apply_safety_margin(limit)
        assert operational == 2550

# ============================================================
# اختبارات التكامل: سيناريوهات واقعية
# ============================================================

class TestIntegrationScenarios:
    """اختبارات تكاملية لسيناريوهات ميدانية واقعية"""
    
    @pytest.fixture
    def pfizer_setup(self):
        library = VaccineLibrary('config/vaccine_library.yaml')
        pfizer = library.get_vaccine('COVID_PFIZER')
        defaults = library.get_defaults()
        engine = DecisionEngine(pfizer, defaults)
        return library, pfizer, defaults, engine
    
    def test_scenario_ideal_storage(self, pfizer_setup):
        """سيناريو 1: تخزين مثالي عند 5°م لمدة 7 أيام"""
        library, pfizer, defaults, engine = pfizer_setup
        
        # بيانات المراقبة: 7 أيام × 24 ساعة × 4 قراءات/ساعة = 672 قراءة
        temps = [5.0] * 672
        intervals = [15] * 672  # كل 15 دقيقة
        
        # حساب MKT
        mkt = calculate_mkt_arrhenius(temps, intervals)
        assert abs(mkt - 5.0) < 0.01
        
        # حساب HER (7 أيام = 168 ساعة، العمر الافتراضي 1680 ساعة)
        profiles = [{'temp_c': 5.0, 'duration_hours': 168}]
        shelf_life = pfizer['storage_phases']['thawed_refrigerated']['shelf_life_hours']
        her = calculate_her_q10(profiles, shelf_life, q10=pfizer['q10_factor'])
        
        assert abs(her - 0.1) < 0.001  # 168/1680 = 0.1
        assert engine.evaluate_her(her) == "✅ مقبول"
        assert engine.evaluate_mkt(mkt) == "✅ مقبول"
    
    def test_scenario_mild_deviation(self, pfizer_setup):
        """سيناريو 2: انحراف خفيف - ساعتان يوميًا عند 12°م لمدة 3 أيام"""
        library, pfizer, defaults, engine = pfizer_setup
        
        # 3 أيام: 66 ساعة عند 5°م + 6 ساعات عند 12°م
        profiles = [
            {'temp_c': 5.0, 'duration_hours': 66},
            {'temp_c': 12.0, 'duration_hours': 6}
        ]
        
        shelf_life = pfizer['storage_phases']['thawed_refrigerated']['shelf_life_hours']
        her = calculate_her_q10(profiles, shelf_life, q10=pfizer['q10_factor'])
        
        # HEI: (12-8) × 6 ساعات × 60 = 4 × 360 = 1440 درجة·دقيقة
        profiles_hei = [
            {'temp_c': 5.0, 'duration_minutes': 66*60},
            {'temp_c': 12.0, 'duration_minutes': 6*60}
        ]
        hei = calculate_hei_linear(profiles_hei)
        
        assert her < 0.85, f"HER {her} يجب أن يكون < 0.85"
        assert hei == 1440, f"HEI المتوقع 1440، لكن حصلنا على {hei}"
        assert engine.evaluate_her(her) in ["✅ مقبول", "⚠️ مراجعة"]
    
    def test_scenario_critical_deviation(self, pfizer_setup):
        """سيناريو 3: انحراف حرج - 4 ساعات عند 25°م"""
        library, pfizer, defaults, engine = pfizer_setup
        
        profiles = [{'temp_c': 25.0, 'duration_hours': 4}]
        shelf_life = pfizer['storage_phases']['thawed_refrigerated']['shelf_life_hours']
        her = calculate_her_q10(profiles, shelf_life, q10=pfizer['q10_factor'])
        
        # HEI: (25-8) × 4 × 60 = 17 × 240 = 4080
        profiles_hei = [{'temp_c': 25.0, 'duration_minutes': 240}]
        hei = calculate_hei_linear(profiles_hei)
        
        # مع Q10=4.0: عامل التسارع = 4^((25-5)/10) = 4^2 = 16
        # التعرض المكافئ = 16 × 4 = 64 ساعة مكافئة عند 5°م
        # HER = 64 / 1680 ≈ 0.038 (لا يزال مقبولاً لهذا الانحراف القصير)
        
        assert hei == 4080, f"HEI المتوقع 4080، لكن حصلنا على {hei}"
        # HER قد يكون مقبولاً لهذا الانحراف القصير، لكن HEI قد يتطلب مراجعة
        assert engine.evaluate_hei(hei) in ["⚠️ مراجعة", "❌ مرفوض"]

# ============================================================
# نقطة الدخول للتشغيل المباشر
# ============================================================

if __name__ == "__main__":
    # تشغيل الاختبارات مباشرة
    pytest.main([
        __file__,
        "-v",           # عرض مفصل
        "--tb=short",   # تتبع مختصر للأخطاء
        "-x"            # التوقف عند أول فشل
    ])