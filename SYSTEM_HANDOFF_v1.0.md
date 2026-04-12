# SYSTEM HANDOFF v1.0 — CCI-FT2 Intelligence
تحليل ومراجعة مدعومة بالكود الفعلي

## الغرض من هذا المستند
هذا الإصدار المحدث من SYSTEM_HANDOFF، مبني على تحليل فعلي للكود في المشروع بدلاً من الاعتماد على التوثيق أو الافتراضات. جميع الادعاءات مدعومة بأدلة من ملفات الكود المحددة.

---

# 1) ما هو هذا النظام؟

بناءً على `src/application/app_composer.py` و `src/application/use_cases/evaluate_cold_chain_safety_use_case.py` و `README.md`:

النظام هو **نظام حراسة معماري** لتحليل بيانات سلسلة تبريد اللقاحات من أجهزة Fridge-tag 2. يحول القراءات الحرارية إلى قرارات تشغيلية/تنظيمية عبر محرك حراري قائم على نموذج Q10/HER مع circuit breakers.

### المخرجات الرئيسية (من `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`):
- تقييم سلامة السلسلة الباردة
- مؤشرات HER ratio و CCM index
- قرارات: SAFE, PARTIAL, DISCARD
- تقارير PDF (عبر `src/application/use_cases/generate_pdf_report_uc.py`)

---

# 2) الفكرة الأساسية التي تحكم النظام

مستمدة من `src/domain/services/exposure_analysis_service.py` و `src/domain/rules/vvm_stage_rule.py`:

## أ) التعرض الحراري تراكمي
يُحسب عبر نموذج Arrhenius (Q10) في `ExposureAnalysisService._calculate_her_ratio()`:
```python
factor = spec.q10_factor ** exponent
cumulative_degradation_hours += duration_hours * factor
her_ratio = cumulative_degradation_hours / spec.shelf_life_hours
```

## ب) بعض الخروقات حاسمة وفورية
Circuit breakers في `ExposureAnalysisService._check_circuit_breakers()`:
- تجمد للقاحات الحساسة (freeze_sensitive=True)
- حرارة >34°C لأكثر من 2 ساعات

## ج) القرار النهائي متعدد المصادر
لا يعتمد على HER وحده، بل يجمع:
- HER ratio
- CCM index
- Circuit breakers
- Rules engine (`src/domain/services/rules_engine.py`)

---

# 3) الخريطة المعمارية المختصرة

بناءً على هيكل المجلدات و `src/application/app_composer.py`:

## الطبقات الأساسية

### 3.1 Domain Layer (`src/domain/`)
**المسؤولية:** القواعد العلمية والحسابات
**الملفات الرئيسية:**
- `services/exposure_analysis_service.py` — محرك التحليل الحراري
- `value_objects/vaccine_specification.py` — مواصفات اللقاحات
- `rules/vvm_stage_rule.py` — قواعد VVM
- `calculators/q10_thermal_calculator.py` — حسابات Q10

### 3.2 Application Layer (`src/application/`)
**المسؤولية:** تنسيق الاستخدامات
**الملفات الرئيسية:**
- `app_composer.py` — تكوين التبعيات
- `use_cases/evaluate_cold_chain_safety_use_case.py` — الاستخدام الرئيسي
- `use_cases/generate_device_report_uc.py` — تقارير الأجهزة
- `use_cases/import_ft2_bundle_uc.py` — استيراد البيانات

### 3.3 Infrastructure Layer (`src/infrastructure/`)
**المسؤولية:** الوصول للبيانات والتقارير
**الملفات الرئيسية:**
- `repositories/device_repository.py`
- `adapters/json_vaccine_spec_repository.py`
- `adapters/reporting/new_pdf_engine.py`

### 3.4 Presentation Layer (`src/presentation/`)
**المسؤولية:** واجهات المستخدم (غير مكتملة حالياً)

---

# 4) نقطة البداية الذهنية الصحيحة

بناءً على الكود الفعلي:

1. `README.md` — الفلسفة والغرض
2. `src/application/app_composer.py` — كيف يتكون النظام
3. `src/application/use_cases/evaluate_cold_chain_safety_use_case.py` — التدفق الرئيسي
4. `src/domain/services/exposure_analysis_service.py` — المنطق العلمي
5. `src/domain/value_objects/vaccine_specification.py` — مصدر الحقيقة للقاحات
6. `config/vaccine_library.yaml` — ⚠️ **يحتوي على اختلافات مع الكود**
7. `tests/unit/test_a1_exposure_analysis.py` — التوقعات الاختبارية

---

# 5) أهم حالات الاستخدام

من `src/application/use_cases/`:

### 5.1 `EvaluateColdChainSafetyUseCase`
**الملف:** `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
**الدور:** الاستخدام الأساسي — يستقبل قراءات ويُنتج قرارات سلامة

### 5.2 `GenerateDeviceReportUseCase`
**الملف:** `src/application/use_cases/generate_device_report_uc.py`
**الدور:** إنتاج تقارير مفصلة للأجهزة

### 5.3 `ImportFT2BundleUseCase`
**الملف:** `src/application/use_cases/import_ft2_bundle_uc.py`
**الدور:** استيراد بيانات FT2 (TXT, PDF)

### 5.4 `GeneratePDFReportUseCase`
**الملف:** `src/application/use_cases/generate_pdf_report_uc.py`
**الدور:** إنتاج تقارير PDF

---

# 6) نقطة التكوين Composition Root

**الملف:** `src/application/app_composer.py`

**الوظيفة:** إنشاء use cases مع حقن التبعيات:
- `DeviceDataRepository`
- `JsonVaccineSpecRepository`
- `RegulatoryDecisionService`
- `ThermalDegradationEstimator`
- `LicenseGuard` (للأمان)

**الطريقة:** static methods لكل use case

---

# 7) القلب العلمي الحالي

### 7.1 `ExposureAnalysisService`
**الملف:** `src/domain/services/exposure_analysis_service.py`

**المسؤوليات:**
1. Circuit breakers (تجمد، حرارة حرجة)
2. حساب HER ratio (Q10)
3. حساب CCM index
4. إرجاع dict موحد

**المخرج:** 
```python
{
    "her_ratio": float,
    "ccm_index": str,  # "0", "A", "B", "C", "ABC", "D"
    "has_freeze": bool,
    "has_critical_heat": bool,
    "circuit_breaker": str or None,
    # ... إحصاءات إضافية
}
```

### 7.2 `VaccineSpecification`
**الملف:** `src/domain/value_objects/vaccine_specification.py`

**المحتوى:** كتالوج Python للقاحات مع:
- `q10_factor`
- `shelf_life_days`
- `freeze_sensitive`
- `vvm_type`

**ملاحظة مهمة:** هناك ازدواجية مع `config/vaccine_library.yaml` — القيم تختلف!

**مثال الاختلاف:**
- BCG في Python: `shelf_life_days=730`
- BCG في YAML: `shelf_life_days: 365`

### 7.3 `VVMStageRule`
**الملف:** `src/domain/rules/vvm_stage_rule.py`

**السلوك:**
- HER >= 1.0 → D (REJECTED_HEAT_C)
- HER >= 0.7 → C
- HER >= 0.4 → B  
- HER >= 0.1 → A
- أقل → NONE

---

# 8) مصدر البيانات والثوابت

### 8.1 ملفات الإعدادات
- `config/thresholds.yaml` — عتبات عامة
- `config/vaccine_library.yaml` — مكتبة لقاحات (لكن غير متزامنة مع الكود!)

### 8.2 المشكلة الحالية
**دليل من الكود:** الازدواجية بين Python و YAML تسبب مخاطر. النظام يستخدم `VACCINE_CATALOGUE` من Python، لكن YAML يحتوي على قيم مختلفة.

---

# 9) كيف يتحول الإدخال إلى قرار؟

من `evaluate_cold_chain_safety_use_case.py`:

1. **استقبال القراءات** → تحويل إلى `TemperatureEntry`
2. **تحليل التعرض** → `ExposureAnalysisService.analyze()`
3. **تطبيق القواعد** → `apply_rules()` مع `VVMStageRule`
4. **دمج Judgment** → `JudgmentEngine.judge()`
5. **إنتاج الاستجابة** → `EvaluateColdChainSafetyResponse`

---

# 10) الملفات التي يجب حفظها

- `src/domain/services/exposure_analysis_service.py`
- `src/domain/value_objects/vaccine_specification.py`
- `src/domain/rules/vvm_stage_rule.py`
- `src/application/app_composer.py`
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
- `config/vaccine_library.yaml` (لكن يحتاج مزامنة!)
- `tests/unit/test_a1_exposure_analysis.py`

---

# 11) ما الذي يعتبر مستقرًا نسبيًا؟

**مستقر:** البنية الطبقية، فصل المسؤوليات، وجود اختبارات للمنطق الأساسي.

**غير مستقر:** تزامن مصادر الحقيقة (Python vs YAML)، اكتمال PDF engine، بعض العتبات.

---

# 12) أين توجد المخاطر الفعلية؟

### 12.1 علمية
- اختلافات بين Python و YAML (مثل shelf_life_days)
- اعتماد على Q10 كتقريب، ليس نموذج تنظيمي كامل

### 12.2 معمارية  
- ازدواجية في مواصفات اللقاحات
- عدم وضوح single source of truth

### 12.3 تشغيلية
- تغيير في `ExposureAnalysisService` يؤثر على كل شيء
- عدم اكتمال PDF reporting

---

# 13) كيف تبدأ التطوير بدون كسر النظام؟

1. اقرأ الاختبارات أولاً (`tests/unit/test_a1_exposure_analysis.py`)
2. حدد العقود من الكود (مثل مفاتيح الـ dict المُرجعة)
3. اختبر أي تغيير على `ExposureAnalysisService`
4. حل مشكلة الازدواجية Python/YAML قبل التوسع

---

# 14) ما الذي يحتاجه النظام قبل الإنتاج؟

1. **توحيد مصدر الحقيقة:** اختيار Python أو YAML كـ single source
2. **تحسين التتبع العلمي:** وثائق لكل ثابت
3. **إكمال PDF engine:** الإصدار الحالي تحت التجديد
4. **تقوية الاختبارات:** integration tests
5. **حل الازدواجية:** مزامنة الكتالوجات

---

# 15) خطة استلام عملية

1. اقرأ `README.md` و `SYSTEM_HANDOFF.md`
2. شغّل الاختبارات (`pytest tests/unit/test_a1_exposure_analysis.py`)
3. افهم `ExposureAnalysisService` و `VaccineSpecification`
4. تحقق من الازدواجية Python/YAML
5. جرب use case بسيط

---

# 16) التوصية النهائية

النظام لديه أساس علمي قوي لكنه يحتاج حل الازدواجية قبل التوسع. `ExposureAnalysisService` و `VaccineSpecification` هما النواة — لا تعدّلهما دون اختبارات شاملة.

---

# ملاحق

## ملحق أ: اختلافات Python vs YAML

| لقاح | خاصية | Python | YAML |
|------|--------|--------|------|
| BCG | shelf_life_days | 730 | 365 |
| BCG | vvm_type | VVM14 | VVM2 |
| MEASLES | shelf_life_days | 730 | 730 ✓ |
| MEASLES | vvm_type | VVM7 | VVM2 |
| HEPB | vvm_type | VVM30 | VVM30 ✓ |
| OPV | vvm_type | VVM2 | VVM2 ✓ |

## ملحق ب: عتبات VVM من الكود

من `vvm_stage_rule.py`:
- A: HER >= 0.1
- B: HER >= 0.4  
- C: HER >= 0.7
- D: HER >= 1.0

## ملحق ج: Circuit Breakers

من `exposure_analysis_service.py`:
- FREEZE: min_temp < -0.5°C للقاحات freeze_sensitive
- CRITICAL_HEAT: hours_above_34 >= 2.0</content>
<parameter name="filePath">/home/amer11974/projects/cci-ft2-intelligence-clean/SYSTEM_HANDOFF_v1.0.md