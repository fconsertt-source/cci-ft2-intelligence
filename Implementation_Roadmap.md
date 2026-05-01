# Implementation Roadmap

## العنوان
خارطة طريق تنفيذية لتحويل نظام `CCI-FT2 Intelligence` من نموذج `Q10/HER approximation` إلى نموذج علمي-تنظيمي صارم قابل للتتبع المرجعي والتكامل الوطني

## 1) الملخص التنفيذي

هذا التقرير يقيّم **قابلية تنفيذ** الخطة المقترحة لتحويل النظام الحالي إلى محرك علمي-تنظيمي أكثر صرامة، مع فصل واضح بين:

- **Regulatory Engine**: يعتمد فقط على نماذج ومعادلات وثوابت موثقة بمرجع أولي.
- **Operational Engine**: يبقي النماذج التقريبية والتشغيلية السريعة مثل `Q10/HER` و`heuristics` للاستخدام اليومي والميداني.

### الحكم المختصر
الخطة **قابلة للتنفيذ من حيث البنية البرمجية**، لأن المشروع الحالي يحتوي أصلًا على نقاط تمديد واضحة في طبقة `domain` و`application`، لكنه **غير قابل للتنفيذ الآمن إذا نُفذ دفعة واحدة** أو إذا دُمجت المتطلبات التنظيمية والبحثية والذكاء الاصطناعي في مسار واحد.

### الاستنتاج الرئيسي
أفضل نهج ليس تنفيذ الخطة كما هي زمنيًا فقط، بل **إعادة ترتيبها إلى مسارين**:

1. **مسار Regulatory Hardening**
   - traceability
   - MKT/Arrhenius formalization
   - constants governance
   - test refactoring
   - citation-backed configuration

2. **مسار Research/AI Augmentation**
   - VTRI-AI
   - LSTM
   - field validation
   - prediction layers
   - dashboard intelligence

هذا الفصل ضروري لأن الكود الحالي يثبت أن النواة الحالية ما زالت مبنية على **تقريب Q10/HER** وليس على **MKT/USP formal model**.

---

## 2) نطاق التقييم والمنهجية

تم بناء هذا التقييم على قراءة مباشرة لملفات الكود والوثائق والاختبارات التالية:

### ملفات الكود الأساسية
- `src/domain/services/exposure_analysis_service.py`
- `src/domain/value_objects/vaccine_specification.py`
- `src/domain/rules/vvm_stage_rule.py`
- `src/domain/services/thermal_degradation_estimator.py`
- `src/domain/calculators/q10_thermal_calculator.py`
- `src/domain/calculators/vvm_q10_model.py`

### ملفات الإعدادات
- `config/thresholds.yaml`
- `config/vaccine_library.yaml`

### الوثائق
- `docs/scientific_models/vvm_q10_model.md`

### الاختبارات
- `tests/unit/test_a1_exposure_analysis.py`
- `tests/unit/domain/rules/test_vvm_stage_rule.py`

---

## 3) الوضع الحالي للنظام: ما الذي ينفذه المشروع فعليًا؟

## 3.1 المحرك العلمي الحالي ليس MKT تنظيميًا بل Q10/HER approximation
في:
- `src/domain/calculators/vvm_q10_model.py`
- `docs/scientific_models/vvm_q10_model.md`

النص الداخلي يصف النموذج بأنه:

- `Q10 (Arrhenius-based approximation)`
- `practical application of the Arrhenius equation principles`

هذا مهم جدًا، لأنه يعني أن النظام الحالي:
- **يستلهم Arrhenius**
- لكنه **لا يطبق MKT وفق USP <1079.2> حرفيًا**
- ولا يطبق kinetic traceability كاملة لكل ثابت/عتبة

## 3.2 قلب التحليل الحراري الحالي
في:
`src/domain/services/exposure_analysis_service.py`

المحرك الحالي يقوم بـ:
1. circuit breakers
2. حساب `HER ratio` عبر `q10_factor`
3. حساب `ccm_index`
4. تمرير النتائج إلى طبقة القرار

الحساب الحالي:

- `factor = spec.q10_factor ** exponent`
- `cumulative_degradation_hours += duration_hours * factor`
- `her_ratio = cumulative_degradation_hours / spec.shelf_life_hours`

هذا منطق تراكمي معقول تشغيليًا، لكنه ليس:
- `compute_mkt()`
- وليس `Ea-driven model`
- وليس `VVM color kinetics formal model`

## 3.3 طبقة القرار الحالية مرتبطة مباشرة بـ HER
في:
`src/domain/rules/vvm_stage_rule.py`

التصنيف الحالي:

- `>= 1.0 -> D`
- `>= 0.7 -> C`
- `>= 0.4 -> B`
- `>= 0.1 -> A`

والاختبارات في:
`tests/unit/domain/rules/test_vvm_stage_rule.py`

تثبت هذا التعاقد مباشرة، ما يعني أن أي استبدال لنموذج `HER` سيكسر:
- السلوك
- الاختبارات
- وربما مخرجات التقارير

## 3.4 وجود تبسيطات صريحة يجب عزلها
في:
`src/domain/services/thermal_degradation_estimator.py`

هناك نص صريح:
- `Simplified Q10 calculation`
- `damage doubles every 10°C above threshold`

وفي:
`src/domain/calculators/q10_thermal_calculator.py`

هناك عتبات تشغيلية غير موثقة سطرًا بسطر مثل:
- `DEFAULT_Q10 = 2.0`
- `DEFAULT_EXCURSION_LIMIT_HOURS = 8.0`
- `factor >= 1.5 -> DISCARD`
- `factor >= 1.2 -> PARTIAL`

هذه الأجزاء تؤكد أن المشروع الحالي **قابل للتطوير** لكنه **غير جاهز بعد لمسار تنظيمي صارم بدون إعادة هيكلة**.

---

## 4) تقييم قابلية تنفيذ الخطة المقترحة

## 4.1 المرحلة 0: التقييم والتوثيق الأساسي
### الحكم
**قابلة للتنفيذ بالكامل ومطلوبة قبل أي تعديل في المعادلات.**

### لماذا هي قابلة للتنفيذ؟
لأن المشروع يحتوي بالفعل على أماكن مركزية للثوابت والمنطق:
- `src/domain/value_objects/vaccine_specification.py`
- `config/vaccine_library.yaml`
- `config/thresholds.yaml`
- `src/domain/services/exposure_analysis_service.py`

### نقاط القوة
- الثوابت ليست مبعثرة بالكامل.
- يوجد كتالوج لقاحات وحقول مثل:
  - `q10_factor`
  - `shelf_life_days`
  - `vvm_type`
  - `critical_temp_c`
  - `critical_hours`
- يوجد metadata ومصادر مذكورة في YAML.

### نقاط الضعف
- التتبع المرجعي الحالي **عام** وليس على مستوى كل ثابت.
- بعض المصادر في YAML مجمعة في سطر واحد وليست:
  - section/page/table-level traceability
- توجد تناقضات بين الكود والإعدادات والاختبارات.

### الأدلة
- `docs/scientific_models/vvm_q10_model.md`: يقر بأن النموذج approximation.
- `config/vaccine_library.yaml`: يضع مصادر عامة لكن ليس لكل قيمة `q10_factor` أو `shelf_life_days` citation granular.
- `config/thresholds.yaml`: يحتوي metadata بمصادر، لكن العتبات نفسها محدودة جدًا ولا تغطي كامل منطق القرار.

### الخلاصة
هذه المرحلة يجب أن تصبح **بوابة دخول إلزامية** قبل أي استبدال للمحرك.

---

## 4.2 المرحلة 1: استبدال المحرك الحراري الأساسي
### الحكم
**قابلة للتنفيذ تقنيًا، لكنها عالية المخاطر إذا تم الاستبدال المباشر داخل المسار الحالي.**

### لماذا هي ممكنة؟
لأن الكود الحالي معزول نسبيًا:
- `src/domain/calculators/vvm_q10_model.py`
- `src/domain/services/exposure_analysis_service.py`
- `src/domain/value_objects/vaccine_specification.py`

وهذا يسمح بإضافة:
- `mkt_calculator.py`
- `arrhenius_kinetics_calculator.py`
- `activation_energy_registry.py`

بدون تدمير كل النظام دفعة واحدة.

### نقاط القوة
- توجد طبقة `calculators` أصلًا.
- توجد طبقة `services` منفصلة عن `rules`.
- توجد مواصفات لقاح قابلة للتوسعة.
- يمكن إضافة `Ea`, `reference_temp_mode`, `kinetic_model` في config/YAML.

### نقاط الضعف
- `ExposureAnalysisService` اليوم يحسب HER مباشرة ويعيده كمفتاح متوقع في أماكن متعددة.
- `VVMStageRule` وtests الحالية مرتبطة بـ `her_ratio`.
- إدخال `compute_mkt()` وحده لا يكفي؛ يجب إعادة تعريف:
  - data contracts
  - result schema
  - decision thresholds
  - backward compatibility

### مخاطر تنفيذية
1. كسر واجهات العقود الحالية:
   - `analyze()` يعيد `her_ratio`
2. كسر الاختبارات الحالية:
   - `tests/unit/test_a1_exposure_analysis.py`
   - `tests/unit/domain/rules/test_vvm_stage_rule.py`
3. خلط `MKT` التنظيمي مع `HER` التشغيلي في نفس المخرجات

### التوصية
بدل **استبدال** المحرك:
- أضف أولًا **محركًا موازيًا**:
  - `src/domain/calculators/mkt_calculator.py`
  - `src/domain/services/regulatory_exposure_analysis_service.py`
- واجعل `Q10/HER` يبقى active كمسار legacy إلى أن تكتمل التغطية المرجعية والاختبارات.

---

## 4.3 المرحلة 2: تحسين نموذج التعرض والتصنيف
### الحكم
**قابلة للتنفيذ ولكن تعتمد كليًا على نجاح المرحلة 0 و1.**

### نقاط القوة
- المواضع المتأثرة محددة بوضوح:
  - `src/domain/services/exposure_analysis_service.py`
  - `src/domain/services/thermal_degradation_estimator.py`
  - `src/domain/rules/vvm_stage_rule.py`

### نقاط الضعف
- الخطة تقترح الانتقال من `HER ratio` إلى `Cumulative Equivalent Time` و`Days to Discard`.
- هذا يعني أن طبقة القرار الحالية لن تعود صالحة كما هي.
- `VVMStageRule` مبني اليوم على thresholds بسيطة `0.1/0.4/0.7/1.0`.
- لا يوجد حاليًا object موحد يمثل:
  - `MKT`
  - `equivalent exposure`
  - `remaining budget`
  - `days_to_discard`
  - `regulatory trace refs`

### ملاحظة حرجة
الاقتراح بإضافة:
- `estimate_days_to_discard()`
- circuit breakers جديدة
- توحيد `10°C vs 12°C`

هو اقتراح صحيح مبدئيًا، لكن يجب أولًا حل تناقضات النظام الحالي.

### الأدلة على التناقض
في:
`src/domain/value_objects/vaccine_specification.py`
- توجد ثوابت باسم:
  - `CCM_WINDOW_A_DAYS_AT_12C`
  - `CCM_WINDOW_AB_DAYS_AT_12C`
  - `CCM_WINDOW_ABC_DAYS_AT_12C`

لكن في:
`src/domain/services/exposure_analysis_service.py`
- العتبة الفعلية:
  - `_CCM_UPPER_THRESHOLD = 10.0`

وفي:
`tests/unit/test_a1_exposure_analysis.py`
- الاختبارات تؤكد سلوك `>10°C`

إذًا المرحلة 2 يجب أن تبدأ أولًا بـ:
- **reconciliation sprint**
- لتحديد المرجع النهائي قبل تعديل المنطق

---

## 4.4 المرحلة 3: بناء VTRI-AI الهجين ودمج الذكاء الاصطناعي
### الحكم
**قابلة نظريًا، لكنها غير مناسبة كجزء مبكر من خارطة الطريق التنظيمية.**

### السبب
إدخال:
- `LSTM`
- `VTRI_AI`
- predictive layer
- validation pipeline

قبل تثبيت:
- traceability
- formal equations
- regulatory contracts

سيؤدي إلى:
- تضخم scope
- صعوبة في التحقق
- خلط بين inference وdecision logic
- إضعاف القابلية التنظيمية بدل تقويتها

### التوصية
يجب **تأجيل هذه المرحلة** إلى ما بعد تثبيت:
1. MKT calculator
2. Ea registry
3. citation-backed thresholds
4. regulatory output schema
5. test suite مستقرة

### أين يمكن دمجها لاحقًا؟
في مسار منفصل:
- `src/domain/services/operational_engine.py`
- أو `src/infrastructure/ml/`
- أو `src/application/use_cases/predict_vvm_remaining_life_use_case.py`

---

## 4.5 المرحلة 4: التحقق والتوثيق والتكامل
### الحكم
**ضرورية وممكنة، لكن يجب تقسيمها إلى تحققين منفصلين:**
1. verification هندسي داخلي
2. validation علمي/ميداني خارجي

### نقاط القوة
- المشروع بالفعل يحتوي نواة اختبار جيدة.
- يوجد فصل طبقات يمكن دعمه بمزيد من golden tests.
- يمكن تمديد التقارير.

### نقاط الضعف
- الاختبارات الحالية تختبر المنطق القديم، لا الجديد.
- لا توجد بعد طبقة traceability آلية.
- لا توجد بنية evidence package واضحة للتدقيق التنظيمي.

---

## 4.6 المرحلة 5: التكامل الوطني والنشر
### الحكم
**غير واقعية قبل إغلاق الفجوات المرجعية والاختبارية.**

### السبب
لا يمكن الانتقال إلى:
- firmware integration
- national rollout
- WHO/PQS proposal

قبل إثبات:
- source-of-truth للثوابت
- reproducible calculations
- cross-version stability
- explicit distinction between advisory vs regulatory outputs

---

## 5) نقاط القوة في الخطة المقترحة

1. **تلتقط المشكلة الحقيقية بدقة**
   - النظام الحالي approximation
   - الهدف المطلوب regulatory-grade

2. **تدعو إلى traceability matrix**
   - وهذا هو العنصر الأهم فعليًا

3. **تعترف بالحاجة إلى MKT/Arrhenius formalization**
   - وهو غائب في الكود الحالي

4. **تعالج التناقض بين التشغيلي والتنظيمي**
   - عبر فصل `regulatory_engine` و`operational_engine`

5. **تضيف مفاهيم تشغيلية ذات قيمة**
   - `days_to_discard`
   - `remaining life`
   - dashboard/reporting

6. **تلتفت إلى التحقق الميداني**
   - وهو ضروري لأي ادعاء وطني

---

## 6) نقاط الضعف في الخطة المقترحة

1. **تجمع المسار التنظيمي والبحثي والذكاء الاصطناعي في خطة واحدة**
2. **تفترض وجود جاهزية مرجعية لبعض الثوابت غير الموجودة حاليًا في الكود**
3. **لا تضع بوابات قرار Go/No-Go كافية**
4. **لا تفصل بين migration-safe changes وbreaking changes**
5. **تتجاوز أثر الاختبارات الحالية**
6. **تتعامل مع LSTM وكأنه تابع طبيعي، بينما هو مشروع مستقل فعليًا**
7. **لا تحدد عقدة التوافق الخلفي للـ APIs وDTOs**
8. **لا تحدد strategy لإزالة الازدواج بين YAML والكود hardcoded values**

---

## 7) الملفات المتأثرة بالخطة ولماذا

## 7.1 ملفات يجب تعديلها أو استبدالها مباشرة
### `src/domain/services/exposure_analysis_service.py`
- لأنه القلب الحالي لحساب `HER`, `CCM`, `circuit_breakers`
- سيتأثر بإضافة:
  - `MKT`
  - `Equivalent Exposure`
  - `Regulatory Analysis Output`

### `src/domain/value_objects/vaccine_specification.py`
- لأنه يحمل:
  - `q10_factor`
  - `shelf_life_days`
  - `vvm_type`
  - `critical_*`
- وسيحتاج حقولًا مثل:
  - `activation_energy_kj_mol`
  - `mkt_window_hours`
  - `regulatory_source_ref`
  - `operational_source_ref`
  - `reaction_rate_model`

### `src/domain/rules/vvm_stage_rule.py`
- لأنه اليوم مربوط مباشرة بـ `her_ratio`
- وسيحتاج إما:
  - استبدال
  - أو تفريع:
    - `vvm_stage_rule_operational.py`
    - `vvm_stage_rule_regulatory.py`

### `src/domain/services/thermal_degradation_estimator.py`
- لأنه يحتوي تبسيطات صريحة يجب عزلها أو إعادة تعريفها كـ advisory only

### `src/domain/calculators/q10_thermal_calculator.py`
- لأنه يحتوي heuristics تشغيلية ستحتاج:
  - توثيق
  - أو عزل
  - أو demotion من regulatory path

### `src/domain/calculators/vvm_q10_model.py`
- لأنه سيصبح:
  - legacy approximation
  - أو optional operational calculator

## 7.2 ملفات جديدة موصى بها
### `src/domain/calculators/mkt_calculator.py`
- لتنفيذ MKT وفق الصيغة المعتمدة

### `src/domain/calculators/arrhenius_calculator.py`
- لحسابات `Ea`, `R`, `equivalent rate`, `kinetic exposure`

### `src/domain/services/regulatory_exposure_analysis_service.py`
- لفصل التحليل التنظيمي عن التشغيلي

### `src/domain/value_objects/regulatory_analysis_result.py`
- لعقدة مخرجات جديدة واضحة

### `src/domain/value_objects/traceability_reference.py`
- لربط كل ثابت بمصدره

### `docs/traceability/Traceability_Matrix.md`
- مرجع Markdown داخل repo

### `docs/scientific_models/regulatory_mkt_model.md`
- توصيف علمي رسمي للمحرك الجديد

### `docs/scientific_models/operational_q10_model.md`
- لتثبيت مكان النموذج القديم بشكل منضبط

## 7.3 ملفات يجب مراجعتها لاختبارات/تكامل
### `tests/unit/test_a1_exposure_analysis.py`
- ستنكسر لأن الحساب الحالي متوقع بدقة

### `tests/unit/domain/rules/test_vvm_stage_rule.py`
- ستنكسر إذا تغير contract من HER إلى metric جديد

### أي use case أو DTO يعتمد `her_ratio`
- لأن schema الحالية ستتوسع أو تتغير

---

## 8) تناقضات حالية يجب حلها قبل أي تطوير كبير

## 8.1 تناقض العتبات 10°C مقابل 12°C
- في `vaccine_specification.py` توجد أسماء constants تشير إلى `12C`
- في `exposure_analysis_service.py` التطبيق الفعلي على `10.0`
- في الاختبارات يتم إثبات سلوك `>10°C`

**الأثر:** لا يمكن بناء traceability محكمة فوق أساس غير موحد.

## 8.2 تناقض catalog بين YAML والكود
`config/vaccine_library.yaml` و`src/domain/value_objects/vaccine_specification.py`
يحتويان معلومات متداخلة وقد لا تكون متطابقة تمامًا.

أمثلة مرصودة:
- في الكود:
  - `MEASLES -> VVM7`
- في YAML:
  - `MEASLES -> VVM2`

- في الكود:
  - `BCG -> VVM14`
- في YAML:
  - `BCG -> VVM2`

- في الكود:
  - `DTP -> VVM14`
- في YAML:
  - `DTP -> VVM30`

**الأثر:** هذا أكبر سبب يمنع traceability موثوقة الآن.

## 8.3 وجود مصادر عامة لا تكفي لاعتماد تنظيمي
في YAML توجد مصادر مثل:
- `WHO/IVB/06.10`
- `CDC`
- `UNICEF`
لكن لا توجد غالبًا:
- table number
- section number
- page number
- exact parameter provenance

---

## 9) خارطة طريق محسّنة مقترحة

## Phase A — Baseline Freeze and Traceability Foundation
### الهدف
تثبيت خط أساس موثق قبل تعديل أي معادلة.

### المخرجات
1. `docs/traceability/Traceability_Matrix.md`
2. `docs/traceability/Traceability_Matrix.csv`
3. `docs/traceability/Current_Model_Gap_Analysis.md`
4. inventory كامل لكل:
   - constant
   - threshold
   - equation
   - source
   - file path

### معايير القبول
- لا يوجد ثابت حاكم بدون مرجع أو status = `UNVERIFIED`
- تم حصر كل التناقضات بين:
  - code
  - YAML
  - tests
  - docs

### Go/No-Go
- **No-Go** إذا بقيت تناقضات catalog غير محسومة

---

## Phase B — Source of Truth Consolidation
### الهدف
إزالة ازدواجية الحقائق العلمية بين الكود وYAML.

### المخرجات
1. اعتماد مصدر موحد:
   - إما YAML
   - أو generated Python objects منه
2. إزالة duplication بين:
   - `VACCINE_CATALOGUE`
   - `config/vaccine_library.yaml`

### معايير القبول
- كل لقاح له تعريف واحد فقط authoritative
- tests تقارن against source-of-truth واحد

### Go/No-Go
- **No-Go** إذا بقيت أنواع VVM أو shelf life مختلفة بين ملفين

---

## Phase C — Parallel Regulatory Engine Introduction
### الهدف
إضافة محرك جديد بدون كسر المحرك الحالي.

### المخرجات
1. `mkt_calculator.py`
2. `arrhenius_calculator.py`
3. `regulatory_exposure_analysis_service.py`
4. `regulatory_analysis_result.py`

### مبدأ التنفيذ
- لا يتم حذف `Q10/HER`
- لا يتم استبدال `analyze()` القديمة فورًا
- يتم تشغيل المحركين بالتوازي في بيئة اختبارية

### معايير القبول
- يمكن مقارنة:
  - `operational_result`
  - `regulatory_result`
- نفس dataset ينتج تقرير مقارنة واضح

### Go/No-Go
- **No-Go** إذا لم يمكن تفسير الفروقات بين المحركين

---

## Phase D — Decision Layer Refactor
### الهدف
فصل القرار التشغيلي عن القرار التنظيمي.

### المخرجات
1. قواعد قرار منفصلة
2. schema مخرجات موسعة
3. reason codes جديدة

### معايير القبول
- كل قرار يحمل:
  - metric source
  - model type
  - reference provenance
- لا يوجد خلط بين `advisory` و`regulatory`

---

## Phase E — Reporting and Days-to-Discard
### الهدف
إضافة مخرجات تشغيلية عالية القيمة دون المساس بنقاء المحرك التنظيمي.

### المخرجات
1. `estimate_days_to_discard()`
2. reporting fields:
   - `remaining_budget_pct`
   - `equivalent_days_at_reference`
   - `predicted_vvm_stage`
   - `days_to_discard`

### معايير القبول
- كل ناتج مشتق موثق بالمعادلة والمصدر
- كل output عليه label:
  - `regulatory`
  - أو `operational`

---

## Phase F — Research / AI Track
### الهدف
إضافة VTRI-AI وLSTM كطبقة مستقلة.

### المخرجات
1. `research_model_spec.md`
2. dataset spec
3. training pipeline
4. inference isolation

### معايير القبول
- لا يعتمد القرار التنظيمي على LSTM
- LSTM يقدم:
  - forecast
  - anomaly prediction
  - operational prioritization
فقط

### Go/No-Go
- **No-Go** إذا لم توجد بيانات ميدانية حقيقية كافية

---

## Phase G — External Validation and National Readiness
### الهدف
إثبات الجاهزية الوطنية بعد استقرار المحرك.

### المخرجات
1. validation dossier
2. traceability pack
3. versioned scientific release
4. dashboard prototype

---

## 10) التوصية النهائية حول LSTM وVTRI-AI

### التوصية الصريحة
**لا تجعل LSTM جزءًا من المسار التنظيمي الأول.**

### السبب
الجهات التنظيمية تحتاج أولًا:
- ثوابت موثقة
- equations reproducible
- deterministic calculations
- auditability

بينما LSTM:
- احتمالي
- يحتاج dataset ميداني كبير
- يضيف تعقيد تفسير
- يبطئ الاعتماد الأساسي

### الموضع الصحيح له
- `Operational Forecasting`
- `Failure prediction`
- `FEFO prioritization`
- `field anomaly scoring`

وليس:
- discard decision primary logic

---

## 11) ما الذي سيكسر إذا نُفذت الخطة كما هي بدون عزل؟

1. اختبارات `ExposureAnalysisService`
2. اختبارات `VVMStageRule`
3. أي contract يعتمد `her_ratio` كمقياس رئيسي
4. التوافق بين التقارير القديمة والجديدة
5. التوقعات المبنية على `ccm_index` الحالية
6. أي واجهة تربط `SAFE/PARTIAL/DISCARD` مباشرة بعتبات Q10 الحالية

---

## 12) القرار التنفيذي المقترح

### القرار
اعتماد الخطة **من حيث الاتجاه الاستراتيجي**، لكن **رفض تنفيذها كحزمة واحدة**.

### القرار البديل المعتمد
تنفيذها عبر ثلاث بوابات رئيسية:

#### Gate 1 — Scientific Traceability Readiness
- حصر
- توثيق
- توحيد
- reconciliation

#### Gate 2 — Parallel Regulatory Engine Readiness
- إضافة MKT/Arrhenius formal engine
- تشغيل موازٍ
- comparative validation

#### Gate 3 — National/Research Expansion
- days to discard
- dashboard
- AI
- field validation
- publication

---

## 13) أولويات التنفيذ الفعلية للأسبوعين الأولين

### أسبوع 1
1. إنشاء traceability matrix
2. توحيد source of truth
3. حل تناقضات:
   - VVM types
   - shelf life
   - thresholds
4. تصنيف الملفات إلى:
   - regulatory
   - operational
   - legacy
   - research

### أسبوع 2
1. تصميم `RegulatoryAnalysisResult`
2. تصميم `mkt_calculator.py`
3. تصميم `activation_energy_registry`
4. إضافة golden comparison tests
5. إبقاء `Q10/HER` دون حذف

---

## 14) الخلاصة النهائية

الخطة المقترحة **قوية استراتيجيًا** لأنها تستهدف المشكلة الصحيحة: رفع المشروع من نموذج تشغيلي مفيد إلى نموذج قابل للتتبع المرجعي والاعتماد التنظيمي.  
لكنها **بحالتها الحالية واسعة أكثر من اللازم** وتدمج ثلاث مبادرات مختلفة في مسار واحد:

1. hardening تنظيمي
2. إعادة هيكلة معمارية
3. ابتكار بحثي/ذكاء اصطناعي

الكود الحالي يدعم هذا التحول من حيث البنية، لكنه لا يدعم تنفيذه دفعة واحدة بأمان.  
النجاح يعتمد على:

- تثبيت traceability أولًا
- توحيد source-of-truth ثانيًا
- إدخال `Regulatory Engine` كمحرك موازٍ ثالثًا
- تأجيل `VTRI-AI/LSTM` إلى مسار لاحق مستقل

### الخلاصة التنفيذية
**الخطة قابلة للتنفيذ، لكن فقط إذا أُعيد ترتيبها إلى roadmap مرحلية ذات بوابات قرار واضحة، مع عزل كامل بين التنظيمي والتشغيلي والبحثي.**
