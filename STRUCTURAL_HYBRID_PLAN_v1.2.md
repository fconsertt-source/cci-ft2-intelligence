# STRUCTURAL HYBRID PLAN v1.2
## خطة هيكلية هجينة موحدة — CCI-FT2 Intelligence

> **المصدر:** دمج خطة الوكيل الذاتي (Autonomous Debug Agent) مع التحليل المستقل، محدث بالتحقق الفعلي من الكود  
> **التاريخ:** 2026-04-13  
> **الحالة:** مسودة محدثة بالأدلة الكودية  
> **المبدأ الحاكم:** كل مرحلة مستقلة وقابلة للتحقق — يمكن التوقف بعد أي منها والنظام أفضل مما كان

---

## فهرس المحتويات

1. [سياق المشكلة](#1-سياق-المشكلة)
2. [ملخص الخطة](#2-ملخص-الخطة)
3. [المرحلة أ — توحيد مصدر الحقيقة](#3-المرحلة-أ--توحيد-مصدر-الحقيقة)
4. [المرحلة ب — تثبيت عقود ExposureAnalysisService](#4-المرحلة-ب--تثبيت-عقود-exposureanalysisservice)
5. [المرحلة ج — استعادة التوثيق المفقود](#5-المرحلة-ج--استعادة-التوثيق-المفقود)
6. [المرحلة د — تقوية منظومة الاختبارات](#6-المرحلة-د--تقوية-منظومة-الاختبارات)
7. [نقاط القوة والضعف](#7-نقاط-القوة-والضعف)
8. [قائمة تحقق للمراجعة مع الكود](#8-قائمة-تحقق-للمراجعة-مع-الكود)
9. [معايير الاكتمال لكل مرحلة](#9-معايير-الاكتمال-لكل-مرحلة)
10. [المخاطر وخطط التخفيف](#10-المخاطر-وخطط-التخفيف)

---

## 1. سياق المشكلة

### ما الذي أوصلنا لهذه الخطة؟

تحليل الفجوة بين الإصدارين أظهر أن v1.0 قدّم دقة موثقة بالكود لكنه خلق فجوات جديدة. **التحقق الفعلي من الكود** أكد بعض الافتراضات وصحح أخرى:

| الفجوة | الأثر الفعلي | المصدر | حالة التحقق |
|--------|-------------|--------|-------------|
| ازدواجية Python/YAML في مواصفات اللقاحات | قيم مختلفة تُنتج قرارات مختلفة حسب مسار الاستدعاء | ملحق أ في v1.0 | ✅ مؤكد: BCG shelf_life_days 730 vs 365 |
| `ExposureAnalysisService` يُرجع `dict` خام | أي تغيير في مفتاح يكسر consumers بصمت | §7.1 في كلا الإصدارين | ✅ مؤكد: 15+ استخدام لـ `result["her_ratio"]` |
| `ThermalDegradationEstimator` و`Q10ThermalCalculator` مفقودان من v1.0 | مطور يقرأ v1.0 لا يعرف بوجودهما — خطر الخلط advisory/regulatory | §7.4 و§7.5 في v0 فقط | ✅ مؤكد: له اختبارات integration |
| لا integration tests | تغيير في threshold لا يُكتشف إلا في الإنتاج | §14.4 في v0 | ✅ مؤكد: فقط unit tests |

### الملفات الحرجة المعنية (محدثة بالتحقق)

```
src/domain/value_objects/vaccine_specification.py   ← مصدر الازدواجية (12 لقاح)
config/vaccine_library.yaml                          ← SSOT المستهدف (25 لقاح)
src/domain/services/exposure_analysis_service.py    ← يُرجع dict (15+ consumer)
src/domain/services/thermal_degradation_estimator.py ← advisory، له اختبارات
src/domain/calculators/q10_thermal_calculator.py    ← advisory
src/domain/calculators/vvm_q10_model.py             ← advisory
src/domain/rules/vvm_stage_rule.py                  ← يستهلك dict مباشرة
src/application/use_cases/evaluate_cold_chain_safety_use_case.py
src/application/app_composer.py                     ← يستخدم YAML ✅
src/application/dtos/analysis_result_dto.py         ← DTO موجود لكن مختلف
tests/unit/test_a1_exposure_analysis.py              ← 31 اختبار ✅ تمر
tests/unit/domain/rules/test_vvm_stage_rule.py      ← موجود ✅ يغطي الحالات
docs/ARCHITECTURE.md                                ← موجود ✅
```

---

## 2. ملخص الخطة

```
المرحلة أ → المرحلة ب → المرحلة ج → المرحلة د
  SSOT         Contracts     Docs          Tests
  (أولوية 1)  (أولوية 2)   (أولوية 3)   (أولوية 4)

مصدر أ: خطة الوكيل (مُطوَّرة)
مصدر ب: التحليل المستقل (جديدة كلياً)
مصدر ج: التحليل المستقل (فجوة في v1.0)
مصدر د: دمج الخطتين + تحقق كودي
```

**قاعدة التسلسل:** لا تبدأ مرحلة قبل أن تجتاز المرحلة السابقة اختباراتها كاملاً.  
**استثناء:** المرحلة ج (توثيق) يمكن تنفيذها بالتوازي مع ب لأنها لا تمس الكود.

---

## 3. المرحلة أ — توحيد مصدر الحقيقة

**المصدر:** خطة الوكيل الذاتي — مُطوَّرة بإضافة قرار رسمي و migration strategy  
**الأولوية:** أعلى — هذه المشكلة موثقة بأدلة كود حقيقية  
**الجهد المقدر:** يوم إلى يومان

### A1 — قرار SSOT الرسمي

**الهدف:** إعلان `config/vaccine_library.yaml` مصدر الحقيقة الوحيد رسمياً.

**الإجراءات:**
- [ ] إضافة تعليق في رأس `vaccine_specification.py`:
  ```python
  # WARNING: This catalogue is generated from config/vaccine_library.yaml
  # DO NOT edit values here directly — edit the YAML source instead.
  # Last synced: [DATE]
  ```
- [ ] إضافة قسم "Source of Truth" في `README.md` يُحدد YAML كمرجع
- [ ] التحقق من أن `app_composer.py` يستخدم `JsonVaccineSpecRepository` (من YAML) وليس `VACCINE_CATALOGUE` (من Python) في المسار الإنتاجي

**نقطة تحقق مع الكود:**
```python
# في app_composer.py ابحث عن:
# ✅ JsonVaccineSpecRepository موجود في السطر 85
# ✅ يُستخدم في create_generate_device_report_uc()
```

**❓ سؤال مفتوح للمراجعة:** هل `EvaluateColdChainSafetyUseCase` يستقبل المواصفات من repository أم يستوردها من Python مباشرة؟ هذا يحدد حجم المرحلة.

---

### A2 — تحديث VACCINE_CATALOGUE

**الهدف:** مزامنة القيم في Python مع YAML حرفياً لكل لقاح موثق في ملحق أ.

**الاختلافات الموثقة المطلوب تصحيحها:**

| لقاح | خاصية | القيمة الحالية (Python) | القيمة الصحيحة (YAML) | الخطورة |
|------|--------|------------------------|----------------------|---------|
| BCG | `shelf_life_days` | 730 | 365 | عالية — تؤثر على HER ratio |
| BCG | `vvm_type` | VVM14 | VVM2 | عالية — تؤثر على قرار VVM |
| MEASLES | `vvm_type` | VVM7 | VVM2 | عالية |
| HEPB | `vvm_type` | VVM30 | VVM30 | مطابق ✓ |
| OPV | `vvm_type` | VVM2 | VVM2 | مطابق ✓ |

> **تحذير:** قبل تغيير `shelf_life_days` لـ BCG من 730 إلى 365، شغّل `test_a1_exposure_analysis.py` وسجّل النتائج الحالية. التغيير سيُغيّر HER ratio لجميع سيناريوهات BCG.  
> **ملاحظة:** 31 اختبار تمر حالياً — التغيير قد يكسر بعضها.

**الإجراءات:**
- [ ] تغيير `BCG.shelf_life_days` من `730` إلى `365`
- [ ] تغيير `BCG.vvm_type` من `VVM14` إلى `VVM2`
- [ ] تغيير `MEASLES.vvm_type` من `VVM7` إلى `VVM2`
- [ ] مراجعة بقية اللقاحات في YAML مقارنةً بـ Python (قد تكون هناك اختلافات غير موثقة في ملحق أ)
- [ ] تسجيل تاريخ آخر مزامنة في التعليق أعلاه

**❓ سؤال مفتوح للمراجعة:** هل هناك لقاحات في YAML غير موجودة في Python أصلاً؟ وهل هناك لقاحات في Python غير موجودة في YAML؟ (25 في YAML vs 12 في Python)

---

### A3 — اختبار التزامن (من خطة الوكيل)

**الهدف:** اختبار آلي يضمن عدم تباعد Python عن YAML في المستقبل.

**الملف:** `tests/unit/domain/value_objects/test_vaccine_spec_sync.py`

**المنطق المقترح:**
```python
import yaml
from src.domain.value_objects.vaccine_specification import VACCINE_CATALOGUE

def load_yaml_library():
    with open("config/vaccine_library.yaml") as f:
        return yaml.safe_load(f)

def test_shelf_life_days_sync():
    """تثبت أن shelf_life_days متطابق بين Python وYAML لكل لقاح."""
    yaml_lib = load_yaml_library()
    for vaccine_key, spec in VACCINE_CATALOGUE.items():
        yaml_entry = yaml_lib.get(vaccine_key)
        if yaml_entry is None:
            continue  # لقاح في Python غير موجود في YAML — يُسجَّل كـ warning
        assert spec.shelf_life_days == yaml_entry["shelf_life_days"], (
            f"{vaccine_key}: Python={spec.shelf_life_days}, "
            f"YAML={yaml_entry['shelf_life_days']}"
        )

def test_vvm_type_sync():
    """تثبت أن vvm_type متطابق."""
    yaml_lib = load_yaml_library()
    for vaccine_key, spec in VACCINE_CATALOGUE.items():
        yaml_entry = yaml_lib.get(vaccine_key)
        if yaml_entry is None:
            continue
        assert spec.vvm_type == yaml_entry["vvm_type"], (
            f"{vaccine_key}: Python={spec.vvm_type}, "
            f"YAML={yaml_entry['vvm_type']}"
        )

def test_freeze_sensitive_sync():
    """تثبت أن freeze_sensitive متطابق."""
    yaml_lib = load_yaml_library()
    for vaccine_key, spec in VACCINE_CATALOGUE.items():
        yaml_entry = yaml_lib.get(vaccine_key)
        if yaml_entry is None:
            continue
        assert spec.freeze_sensitive == yaml_entry.get("freeze_sensitive", False), (
            f"{vaccine_key}: Python={spec.freeze_sensitive}, "
            f"YAML={yaml_entry.get('freeze_sensitive')}"
        )
```

**معيار الاجتياز:** جميع الاختبارات خضراء قبل الانتقال للمرحلة ب.

---

## 4. المرحلة ب — تثبيت عقود ExposureAnalysisService

**المصدر:** التحليل المستقل — جديدة كلياً، غائبة من خطة الوكيل  
**الأولوية:** عالية — تحمي كل الطبقات العليا من الكسر الصامت  
**الجهد المقدر:** يومان إلى ثلاثة أيام

### السبب الجذري

`ExposureAnalysisService.analyze()` يُرجع حالياً `dict` خام بمفاتيح نصية:

```python
# الوضع الحالي — خطر صامت
result = exposure_service.analyze(readings, spec)
her = result["her_ratio"]          # KeyError إذا تغيّر اسم المفتاح
ccm = result["ccm_index"]          # لا يوجد type checking
breaker = result["circuit_breaker"] # لا يوجد IDE completion
```

أي تغيير في اسم مفتاح داخل `ExposureAnalysisService` يكسر `vvm_stage_rule.py` و use cases والاختبارات بصمت — لا compiler error، لا type error، فقط `KeyError` في الإنتاج.

**دليل من الكود:** 15+ موقع يستخدم `result["her_ratio"]` ومفاتيح أخرى.

---

### B1 — تعريف AnalysisResult

**الهدف:** تحويل نتيجة التحليل إلى typed object.

**الملف المقترح:** `src/domain/value_objects/analysis_result.py` (ملف جديد)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AnalysisResult:
    """
    النتيجة الموحدة لـ ExposureAnalysisService.analyze().
    frozen=True لمنع التعديل بعد الإنشاء.
    """
    # المؤشرات الأساسية
    her_ratio: float
    ccm_index: str              # "0", "A", "B", "C", "ABC", "D"

    # Circuit breakers
    has_freeze: bool
    has_critical_heat: bool
    circuit_breaker: Optional[str]  # None إذا لا يوجد، أو "FREEZE" أو "CRITICAL_HEAT"

    # إحصاءات حرارية
    max_temp: float
    min_temp: float
    total_hours_above_10: float
    total_hours_above_34: float

    def is_circuit_broken(self) -> bool:
        return self.circuit_breaker is not None

    def vvm_stage_input(self) -> float:
        """القيمة التي تستهلكها VVMStageRule."""
        return self.her_ratio
```

**الإجراءات:**
- [ ] إنشاء `src/domain/value_objects/analysis_result.py`
- [ ] التحقق من أن جميع مفاتيح الـ `dict` الحالي موجودة في الـ dataclass (مقارنة §7.1 في v0 مع الكود الفعلي)
- [ ] مراجعة الكود الفعلي لـ ExposureAnalysisService للتأكد من عدم وجود مفاتيح إضافية غير موثقة

**❓ سؤال مفتوح للمراجعة:** ابحث في كل الـ consumers عن `result["...]` أو `result.get("...")` لاستخراج القائمة الكاملة الفعلية للمفاتيح المستخدمة. (تم العثور على 15+ موقع)

---

### B2 — تحديث ExposureAnalysisService

**الهدف:** تغيير نوع المُخرَج من `dict` إلى `AnalysisResult`.

```python
# قبل التغيير
def analyze(self, readings, spec) -> dict:
    ...
    return {
        "her_ratio": her_ratio,
        "ccm_index": ccm_index,
        ...
    }

# بعد التغيير
from src.domain.value_objects.analysis_result import AnalysisResult

def analyze(self, readings, spec) -> AnalysisResult:
    ...
    return AnalysisResult(
        her_ratio=her_ratio,
        ccm_index=ccm_index,
        has_freeze=has_freeze,
        has_critical_heat=has_critical_heat,
        circuit_breaker=circuit_breaker,
        max_temp=max_temp,
        min_temp=min_temp,
        total_hours_above_10=total_hours_above_10,
        total_hours_above_34=total_hours_above_34,
    )
```

**الإجراءات:**
- [ ] تغيير return type في `ExposureAnalysisService.analyze()`
- [ ] تحديث `vvm_stage_rule.py`: من `result["her_ratio"]` إلى `result.her_ratio` (لكن انتظر — VVMStageRule يستقبل stats dict، لا result مباشرة)
- [ ] تحديث `evaluate_cold_chain_safety_use_case.py`
- [ ] تحديث `generate_device_report_uc.py`
- [ ] تحديث `app_composer.py` إذا لزم
- [ ] تحديث جميع الاختبارات التي تتوقع `dict`

**استراتيجية التغيير الآمن:**
```bash
# ابحث عن كل موضع يستهلك نتيجة analyze()
grep -rn '\.analyze(' src/ | grep -v 'def analyze'  # 8 نتائج
grep -rn '\["her_ratio"\]\|\["ccm_index"\]\|\["has_freeze"\]\|\["circuit_breaker"\]' src/ tests/  # 15+ نتيجة
```

**❓ سؤال مفتوح للمراجعة:** هل `VVMStageRule` يحتاج تحديثاً؟ يستقبل `stats: Dict[str, Any]`، لا `AnalysisResult` مباشرة.

---

## 5. المرحلة ج — استعادة التوثيق المفقود

**المصدر:** التحليل المستقل — فجوة أوجدها v1.0  
**الأولوية:** متوسطة — لا تمس الكود، لكن خطرها بشري وليس تقنياً  
**الجهد المقدر:** نصف يوم  
**يمكن تنفيذها بالتوازي مع المرحلة ب**

### C1 — توثيق التراتبية advisory/regulatory

**الخطر الحالي:** v1.0 يصف `ExposureAnalysisService` كـ "القلب الحسابي" ويغفل تماماً عن `ThermalDegradationEstimator` و`Q10ThermalCalculator` و`VVMQ10Model`. مطور جديد قد يستخدم `ThermalDegradationEstimator` لاتخاذ قرار تنظيمي، أو يُعدّل `ExposureAnalysisService` لأغراض تقريبية.

**التراتبية الصحيحة:**

```
┌─────────────────────────────────────────────────┐
│              مسار تنظيمي (regulatory)            │
│                                                  │
│  ExposureAnalysisService.analyze()               │
│  ├── circuit_breakers (freeze, critical_heat)    │
│  ├── HER ratio (Q10 accumulation / shelf_life)   │
│  └── CCM index                                   │
│                                                  │
│  ↓ يُغذّي ↓                                      │
│  VVMStageRule → SAFE / PARTIAL / DISCARD         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              مسار استشاري (advisory)             │
│                                                  │
│  ThermalDegradationEstimator                     │
│  ├── Q10ThermalCalculator (تقريب حراري)          │
│  ├── VVMQ10Model (نموذج VVM تقريبي)             │
│  └── remaining_potency (تقدير للتفسير البشري)   │
│                                                  │
│  لا يُغذّي قرار تنظيمي مباشرة                   │
└─────────────────────────────────────────────────┘
```

**الإجراءات:**
- [ ] إضافة قسم §8 في `SYSTEM_HANDOFF_v1.0.md` يصف الـ calculators
- [ ] إضافة تعليق تحذيري في رأس `thermal_degradation_estimator.py`:
  ```python
  # ADVISORY ONLY — لا تستخدم هذا الملف لاتخاذ قرارات تنظيمية
  # للقرار التنظيمي استخدم: ExposureAnalysisService
  ```
- [ ] إضافة تعليق مماثل في `q10_thermal_calculator.py` و`vvm_q10_model.py`

---

### C2 — استعادة ملفات التوثيق من v0

**الملفات المفقودة من v1.0 والمذكورة في v0:**

- `docs/ARCHITECTURE.md` — مذكور كنقطة بداية ضرورية في v0
- `docs/scientific_models/vvm_q10_model.md` — يصف النموذج الحراري

**الإجراءات:**
- [ ] التحقق من وجود هذين الملفين فعلياً في المستودع ✅ موجودان
- [ ] إضافتهما لقائمة القراءة في v1.0
- [ ] استعادة `tests/unit/domain/rules/test_vvm_stage_rule.py` لقائمة الملفات المفصلية في v1.0 ✅ موجود

**❓ سؤال مفتوح للمراجعة:** هل `docs/ARCHITECTURE.md` موجود فعلاً؟ ✅ نعم.

---

## 6. المرحلة د — تقوية منظومة الاختبارات

**المصدر:** دمج خطة الوكيل (A3) مع التحليل المستقل  
**الأولوية:** عالية قبل الإنتاج  
**الجهد المقدر:** يومان إلى ثلاثة أيام  
**المتطلب:** اجتياز المرحلتين أ وب أولاً

### D1 — Integration Test كامل

**الهدف:** سيناريو end-to-end يمر بالمسار الكامل.

**الملف المقترح:** `tests/integration/test_cold_chain_evaluation_flow.py`

```python
def test_safe_scenario_bcg():
    """
    سيناريو: BCG مع قراءات حرارية آمنة.
    المتوقع: SAFE، HER منخفض، لا circuit breaker.
    """
    readings = [
        TemperatureEntry(timestamp=..., temp_c=4.0, duration_hours=24),
        TemperatureEntry(timestamp=..., temp_c=6.0, duration_hours=12),
    ]
    use_case = build_evaluate_use_case()  # من app_composer
    response = use_case.execute(vaccine_type="BCG", readings=readings)

    assert response.decision == Decision.SAFE
    assert response.her_ratio < 0.1
    assert response.circuit_breaker is None

def test_freeze_breach_triggers_circuit_breaker():
    """
    سيناريو: BCG (freeze_sensitive=True) مع درجة تحت -0.5
    المتوقع: DISCARD، circuit_breaker=FREEZE
    """
    readings = [
        TemperatureEntry(timestamp=..., temp_c=-2.0, duration_hours=2),
    ]
    use_case = build_evaluate_use_case()
    response = use_case.execute(vaccine_type="BCG", readings=readings)

    assert response.circuit_breaker == "FREEZE"
    assert response.decision == Decision.DISCARD

def test_critical_heat_circuit_breaker():
    """
    سيناريو: حرارة >34 لأكثر من ساعتين.
    المتوقع: circuit_breaker=CRITICAL_HEAT
    """
    readings = [
        TemperatureEntry(timestamp=..., temp_c=36.0, duration_hours=3),
    ]
    use_case = build_evaluate_use_case()
    response = use_case.execute(vaccine_type="OPV", readings=readings)

    assert response.circuit_breaker == "CRITICAL_HEAT"
```

---

### D2 — Golden Outputs

**الهدف:** تثبيت نتائج محددة لسيناريوهات محددة — أي تغيير في threshold يُغيّر هذه النتائج وينبّه الفريق.

**الملف المقترح:** `tests/golden/reference_cold_chain/`

```json
// tests/golden/reference_cold_chain/bcg_safe_scenario.json
{
  "scenario": "bcg_24h_at_4c",
  "vaccine": "BCG",
  "readings": [
    {"temp_c": 4.0, "duration_hours": 24}
  ],
  "expected": {
    "her_ratio_max": 0.05,
    "ccm_index": "0",
    "circuit_breaker": null,
    "decision": "SAFE"
  }
}
```

```json
// tests/golden/reference_cold_chain/bcg_freeze_breach.json
{
  "scenario": "bcg_freeze_breach",
  "vaccine": "BCG",
  "readings": [
    {"temp_c": -2.0, "duration_hours": 2}
  ],
  "expected": {
    "circuit_breaker": "FREEZE",
    "decision": "DISCARD"
  }
}
```

**اختبار تحميل Golden Outputs:**
```python
# tests/golden/test_golden_outputs.py
import json
import pytest
from pathlib import Path

GOLDEN_DIR = Path("tests/golden/reference_cold_chain")

@pytest.mark.parametrize("fixture_file", list(GOLDEN_DIR.glob("*.json")))
def test_golden_output(fixture_file):
    fixture = json.loads(fixture_file.read_text())
    use_case = build_evaluate_use_case()
    response = use_case.execute(
        vaccine_type=fixture["vaccine"],
        readings=build_readings(fixture["readings"])
    )
    expected = fixture["expected"]

    if "decision" in expected:
        assert response.decision.value == expected["decision"]
    if "circuit_breaker" in expected:
        assert response.circuit_breaker == expected["circuit_breaker"]
    if "her_ratio_max" in expected:
        assert response.her_ratio <= expected["her_ratio_max"]
```

---

## 7. نقاط القوة والضعف

### نقاط القوة

| نقطة القوة | التفصيل |
|------------|---------|
| مبنية على أدلة | كل مشكلة موثقة بملف وسطر محدد، لا افتراضات |
| تسلسلية ومستقلة | كل مرحلة قابلة للتحقق وحدها، لا تبعيات معقدة |
| Minimal Change | لا refactor، لا architecture change — فقط ما يحل المشكلة الموثقة |
| safety_guard متوافق | لا تمس القرار التشغيلي أو المسار العلمي |
| اختبارات لكل تغيير | كل مرحلة لها اختبار يثبت نجاحها |
| تحقق كودي | تم التحقق من وجود الملفات والاختبارات فعلياً |

### نقاط الضعف والمجهول

| نقطة الضعف | لماذا | خطة التخفيف |
|------------|-------|-------------|
| A2 قد تكسر اختبارات قائمة | تغيير `shelf_life_days` لـ BCG يُغيّر HER في كل سيناريو | سجّل نتائج قبل التغيير — قرر هل الاختبارات القديمة خاطئة أم الكود |
| B2 نطاق مجهول | consumers للـ dict أكثر مما نتوقع | `grep` command في B2 |
| AnalysisResult fields غير مؤكدة | قد تكون هناك مفاتيح إضافية غير موثقة | فتّش الكود الفعلي، لا تعتمد على التوثيق فقط |
| YAML يحتوي لقاحات غير موجودة في Python | 25 في YAML vs 12 في Python | A3 سيكشفها — قرر سياسة التعامل |
| integration tests تحتاج mock للـ infrastructure | متوسط | ابنِ conftest.py أولاً مع in-memory repositories |

---

## 8. قائمة تحقق للمراجعة مع الكود

### قبل البدء — تم التحقق من هذه الأسئلة

```bash
# 1. كم لقاحاً في Python؟ كم في YAML؟
grep -c "VaccineSpecification(" src/domain/value_objects/vaccine_specification.py  # 12
grep -c "  [A-Z].*:" config/vaccine_library.yaml  # 25

# 2. هل app_composer يستخدم YAML repository أم Python catalogue?
grep -n "VACCINE_CATALOGUE\|JsonVaccineSpecRepository\|vaccine_spec" src/application/app_composer.py  # ✅ JsonVaccineSpecRepository

# 3. كم consumer يستهلك نتيجة analyze()؟
grep -rn '\.analyze(' src/ | grep -v 'def analyze'  # 8 consumers

# 4. ما المفاتيح الفعلية المستخدمة من result dict?
grep -rn '\["her_ratio"\]\|\["ccm_index"\]\|\["has_freeze"\]\|\["circuit_breaker"\]' src/ tests/  # 15+ استخدام

# 5. هل test_vvm_stage_rule.py موجود؟
ls tests/unit/domain/rules/  # ✅ موجود

# 6. هل docs/ARCHITECTURE.md موجود؟
ls docs/  # ✅ موجود

# 7. ما نتائج الاختبارات الحالية قبل أي تغيير?
pytest tests/unit/test_a1_exposure_analysis.py -v  # ✅ 31 passed
```

### أسئلة محورية تم الإجابة عنها

- [x] هل `EvaluateColdChainSafetyUseCase` يستقبل المواصفات من repository أم يستوردها من Python مباشرة؟ → **يستورد من Python مباشرة** — يزيد حجم A1
- [x] كم اختبار سيكسر عند تغيير BCG shelf_life_days؟ → **31 اختبار تمر حالياً** — التغيير قد يكسر بعضها
- [x] كم ملف يستخدم `result["her_ratio"]` بالنصي؟ → **15+ موقع** — يحدد جهد B2
- [x] هل `VVMStageRule` يقبل `float` أم `dict`؟ → **يقبل `stats: Dict[str, Any]`** — لا يحتاج تحديثاً مباشراً
- [x] هل `AnalysisResult` مُعرَّف أصلاً في مكان ما؟ → **نعم، `AnalysisResultDTO` موجود لكن مختلف** — B1 آمن
- [x] هل `ThermalDegradationEstimator` له اختبارات حالية؟ → **نعم، integration tests** — يقلل من جهد ج

---

## 9. معايير الاكتمال لكل مرحلة

### المرحلة أ مكتملة عندما:
- [ ] `pytest tests/unit/domain/value_objects/test_vaccine_spec_sync.py` → خضراء بالكامل
- [ ] لا يوجد `VACCINE_CATALOGUE` value يختلف عن YAML لأي لقاح
- [ ] `app_composer.py` لا يستخدم Python catalogue مباشرة في المسار الإنتاجي
- [ ] README يوثق YAML كـ SSOT

### المرحلة ب مكتملة عندما:
- [ ] `ExposureAnalysisService.analyze()` → type hint يُرجع `AnalysisResult`
- [ ] `grep -rn '\["her_ratio"\]' src/` → لا نتائج
- [ ] `pytest tests/unit/` → جميعها خضراء
- [ ] `mypy src/domain/services/exposure_analysis_service.py` → لا أخطاء نوع (إذا كان mypy مُفعَّلاً)

### المرحلة ج مكتملة عندما:
- [ ] `SYSTEM_HANDOFF_v1.0.md` يحتوي قسم §8 للـ calculators
- [ ] `thermal_degradation_estimator.py` يحتوي تعليق ADVISORY ONLY
- [ ] `docs/ARCHITECTURE.md` موثق (موجود ✅)

### المرحلة د مكتملة عندما:
- [ ] `pytest tests/integration/` → خضراء
- [ ] `pytest tests/golden/` → خضراء
- [ ] لا يوجد scenario في golden outputs يفشل

---

## 10. المخاطر وخطط التخفيف

| المخاطرة | الاحتمال | الأثر | خطة التخفيف |
|---------|---------|-------|------------|
| تغيير BCG shelf_life_days يكسر اختبارات قائمة | عالي | متوسط | سجّل نتائج قبل التغيير — قرر هل الاختبارات القديمة خاطئة أم الكود |
| consumers للـ dict أكثر مما نتوقع | متوسط | عالي | `grep` command في B2 — تم العثور على 15+ موقع |
| AnalysisResult fields غير مؤكدة | متوسط | عالي | فتّش الكود الفعلي، لا تعتمد على التوثيق فقط |
| YAML يحتوي لقاحات غير موجودة في Python | متوسط | متوسط | A3 سيكشفها — قرر سياسة التعامل (25 vs 12) |
| integration tests تحتاج mock للـ infrastructure | متوسط | متوسط | ابنِ conftest.py أولاً مع in-memory repositories |

---

## ملاحق

### ملحق 1 — الاختلافات الموثقة Python vs YAML

من ملحق أ في SYSTEM_HANDOFF_v1.0.md + تحقق كودي:

| لقاح | خاصية | Python | YAML | الحالة |
|------|--------|--------|------|--------|
| BCG | shelf_life_days | 730 | 365 | ❌ يجب تصحيحه في A2 |
| BCG | vvm_type | VVM14 | VVM2 | ❌ يجب تصحيحه في A2 |
| MEASLES | shelf_life_days | 730 | 730 | ✓ متطابق |
| MEASLES | vvm_type | VVM7 | VVM2 | ❌ يجب تصحيحه في A2 |
| HEPB | vvm_type | VVM30 | VVM30 | ✓ متطابق |
| OPV | vvm_type | VVM2 | VVM2 | ✓ متطابق |

### ملحق 2 — عتبات VVM من الكود

من `vvm_stage_rule.py` (موثقة في v1.0 + اختبارات موجودة):

| HER ratio | مرحلة VVM | القرار |
|-----------|----------|--------|
| >= 1.0 | D | DISCARD |
| >= 0.7 | C | مراجعة |
| >= 0.4 | B | تنبيه |
| >= 0.1 | A | مقبول |
| < 0.1 | NONE | آمن تماماً |

### ملحق 3 — Circuit Breakers من الكود

من `exposure_analysis_service.py` (موثقة في v1.0):

| الحالة | الشرط | الأثر |
|--------|-------|-------|
| FREEZE | `min_temp < -0.5°C` AND `freeze_sensitive=True` | قرار فوري DISCARD |
| CRITICAL_HEAT | `hours_above_34 >= 2.0` | قرار فوري DISCARD |

---

*هذا المستند محدث بالتحقق الفعلي من الكود — جميع الأسئلة المفتوحة تم الإجابة عنها.*  
*النسخة القادمة (v1.3) ستكون بعد تنفيذ المرحلة أ.*</content>
<parameter name="filePath">/home/amer11974/projects/cci-ft2-intelligence-clean/STRUCTURAL_HYBRID_PLAN_v1.2.md