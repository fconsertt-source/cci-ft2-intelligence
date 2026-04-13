# SYSTEM HANDOFF — CCI-FT2 Intelligence

## الغرض من هذا المستند
هذا المستند هو وصف عملي ودقيق للنظام، موجّه لأي مبرمج جديد يحتاج إلى:

- فهم ما الذي يفعله النظام فعليًا اليوم
- معرفة أين تبدأ القراءة والتطوير
- فهم مسارات البيانات والقرار
- معرفة الملفات الحساسة
- تمييز ما هو مستقر وما هو انتقالي أو legacy
- استكمال النظام حتى مرحلة الإنتاج دون كسر المعنى العلمي أو المعماري

هذا المستند لا يحاول ترويج المشروع، بل يقدّم **صورة تشغيلية وهندسية صادقة** تساعد على الاستلام السريع والمسؤول.

---

# 1) ما هو هذا النظام؟

`CCI-FT2 Intelligence` هو نظام لتحليل بيانات سلسلة تبريد اللقاحات، خصوصًا بيانات أجهزة `Fridge-tag 2` أو المسارات القريبة منها، بهدف تحويل القراءات الحرارية الخام إلى:

- تقييم أمان/مخاطر
- مؤشرات تعرض حراري
- تقارير جهاز أو مركز أو دفعة
- مخرجات تنظيمية/تشغيلية تساعد في الحكم:
  - صالح
  - تعرض جزئي
  - مرفوض
  - يحتاج مراجعة

## ما الذي لا يفعله النظام حاليًا بدقة؟
رغم اللغة العلمية في بعض الوثائق، النظام الحالي **ليس بعدُ محركًا تنظيميًا صارمًا بالكامل**.  
النواة الحالية تعتمد أساسًا على:

- `Q10/HER approximation`
- بعض `WHO/PQS-style thresholds`
- circuit breakers للتجمد/الحرارة الحرجة
- rules layer لإنتاج القرار

بالتالي يجب على أي مبرمج جديد أن يفهم من البداية:

> النظام الحالي **تشغيلي قوي نسبيًا**، لكنه **ليس بعدُ المرجع العلمي التنظيمي النهائي**.

---

# 2) الفكرة الأساسية التي تحكم النظام

النظام مبني على 3 أفكار مترابطة:

## أ) التعرض الحراري تراكمي
التعرض للحرارة لا يُعالج كمتوسط بسيط، بل كأثر متراكم عبر الزمن.

## ب) بعض الخروقات حاسمة وفورية
مثل:
- التجمّد للقاحات الحساسة للتجمّد
- حرارة شديدة جدًا لفترة حرجة

هذه الحالات تتجاوز منطق التراكم العادي وتُفعّل `circuit breakers`.

## ج) القرار النهائي لا يخرج من calculator واحد فقط
المشروع يفصل بين:
- الحسابات الحرارية
- مؤشرات الحالة
- قواعد القرار
- واجهات التقارير

وهذا هو سبب انتشار المنطق عبر `domain/services`, `domain/rules`, `application/use_cases`, و`infrastructure`.

---

# 3) الخريطة المعمارية المختصرة

المشروع يتبع `Clean Architecture`.

## الطبقات الأساسية

### 3.1 Domain Layer
الموقع:
- `src/domain/`

المسؤولية:
- القواعد الأساسية
- الحسابات الحرارية
- entities
- value objects
- enums
- rules
- domain services

أهم ما ستجده هنا:
- `services/exposure_analysis_service.py`
- `rules/vvm_stage_rule.py`
- `value_objects/vaccine_specification.py`
- `calculators/q10_thermal_calculator.py`
- `calculators/vvm_q10_model.py`
- `services/thermal_degradation_estimator.py`

### 3.2 Application Layer
الموقع:
- `src/application/`

المسؤولية:
- orchestration
- use cases
- DTOs
- composition
- تنسيق نتائج الـ domain إلى مخارج قابلة للاستهلاك

أهم الملفات:
- `app_composer.py`
- `use_cases/evaluate_cold_chain_safety_use_case.py`
- `use_cases/generate_device_report_uc.py`
- `use_cases/import_ft2_bundle_uc.py`
- DTOs المرتبطة بالتقارير والتقييم

### 3.3 Infrastructure Layer
الموقع:
- `src/infrastructure/`

المسؤولية:
- القراءة من الملفات/المخازن
- PDF generation
- repositories
- adapters
- security
- validation integrations

### 3.4 Presentation Layer
الموقع:
- `src/presentation/`

المسؤولية:
- CLI أو GUI أو واجهات التشغيل

> إذا أردت تشغيل النظام end-to-end، لا تبدأ من domain مباشرة؛ ابدأ من use case أو composer أو script.

---

# 4) نقطة البداية الذهنية الصحيحة لأي مبرمج جديد

ابدأ بفهم النظام من الأعلى إلى الأسفل بهذا الترتيب:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `src/application/app_composer.py`
4. `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
5. `src/domain/services/exposure_analysis_service.py`
6. `src/domain/value_objects/vaccine_specification.py`
7. `src/domain/rules/vvm_stage_rule.py`
8. `config/vaccine_library.yaml`
9. `config/thresholds.yaml`
10. الاختبارات المرتبطة:
   - `tests/unit/test_a1_exposure_analysis.py`
   - `tests/unit/domain/rules/test_vvm_stage_rule.py`

هذا الترتيب يسمح لك بفهم:
- المعمارية
- نقطة التكوين
- حالة الاستخدام الأساسية
- المنطق العلمي الحالي
- مصدر الثوابت
- التوقعات الاختبارية

---

# 5) ما هي أهم حالات الاستخدام الموجودة؟

استنادًا إلى `src/application/use_cases/`، النظام ليس حالة استخدام واحدة، بل عدة مسارات تشغيلية.

## أهم Use Cases الحالية

### 5.1 `EvaluateColdChainSafetyUseCase`
الملف:
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`

هذا هو أقرب Use Case للقلب العلمي للنظام، لأنه:
- يستقبل قراءات حرارة
- يحوّلها إلى model داخلي
- يمررها إلى التحليل الحراري
- يفعّل rules
- ينتج response نهائيًا

إذا أردت فهم الحكم العلمي/التشغيلي، فابدأ من هنا.

### 5.2 `GenerateDeviceReportUseCase`
الملف:
- `src/application/use_cases/generate_device_report_uc.py`

هذا use case مهم للإنتاج لأنه يربط:
- repository
- vaccine specs
- regulatory decision service
- degradation estimator
- validation
- licensing

هذا المسار أقرب إلى تدفق “التقرير الكامل”.

### 5.3 `ImportFT2BundleUseCase`
الملف:
- `src/application/use_cases/import_ft2_bundle_uc.py`

هذا مسار الإدخال الرئيسي للحزم القادمة من FT2:
- TXT
- PDF
- logging
- repository persistence

### 5.4 `GeneratePDFReportUseCase`
الملف:
- `src/application/use_cases/generate_pdf_report_uc.py`

هذا use case يعزل منطق إخراج تقارير PDF.

---

# 6) نقطة التكوين Composition Root

الملف:
- `src/application/app_composer.py`

هذا الملف مهم جدًا لأنه يوضح كيف تتجمع الأجزاء فعليًا عند التشغيل.

## ماذا يفعل؟
ينشئ use cases جاهزة بحقن التبعيات، مثل:
- `GenerateDeviceReportUseCase`
- `GeneratePDFReportUseCase`
- `ImportFT2BundleUseCase`

## ماذا يربط؟
- repository
- vaccine specs repository
- regulatory service
- thermal estimator
- validation service
- license guard

## لماذا هو مهم؟
إذا أردت:
- تتبع wiring الفعلي
- معرفة ما هو مستخدم في الإنتاج
- استبدال implementation بآخر
- إضافة dependency جديدة

فهذا هو أول ملف يجب فحصه.

---

# 7) القلب العلمي الحالي: كيف يعمل النظام اليوم؟

## 7.1 `ExposureAnalysisService`
الملف:
- `src/domain/services/exposure_analysis_service.py`

هذا هو **القلب الحسابي الحالي**.

### مسؤولياته
1. تطبيق circuit breakers
2. حساب `HER ratio`
3. حساب `CCM index`
4. إعادة dict موحد إلى طبقة القرار

### أهم ما يجب فهمه
- النظام الحالي يستخدم `Q10` لحساب عامل التسارع الحراري
- ثم يجمع أثر الانحلال عبر الزمن
- ثم يقسم على `shelf_life_hours`
- لينتج `her_ratio`

### المخرج النموذجي
الخدمة تعيد أشياء من نوع:
- `her_ratio`
- `ccm_index`
- `has_freeze`
- `has_critical_heat`
- `max_temp`
- `min_temp`
- `total_hours_above_10`
- `total_hours_above_34`
- `circuit_breaker`

### لماذا هذا مهم؟
لأن كثيرًا من الطبقات الأعلى تعتمد على هذه المفاتيح مباشرة.  
أي تغيير هنا قد يكسر:
- rules
- use cases
- reports
- tests

---

## 7.2 `VaccineSpecification`
الملف:
- `src/domain/value_objects/vaccine_specification.py`

هذا الملف هو **مصدر الحقيقة البرمجي الحالي** لكثير من خصائص اللقاح.

### يحتوي على
- `q10_factor`
- `shelf_life_days`
- `reference_temp_c`
- `freeze_sensitive`
- `vvm_type`
- `critical_temp_c`
- `critical_hours`
- `rationale`

### يحتوي أيضًا على
- `VACCINE_CATALOGUE`
- `get_vaccine_spec(vaccine_type)`

### لماذا هو حساس جدًا؟
لأن تغييرات هذا الملف تؤثر على:
- التحليل الحراري
- circuit breakers
- نوع VVM
- الاختبارات
- التوافق مع YAML

### ملاحظة مهمة
يوجد أيضًا ملف YAML:
- `config/vaccine_library.yaml`

وفي الوضع الحالي هناك إشارات قوية إلى احتمال وجود **ازدواجية أو عدم تطابق** بين:
- القيم داخل Python
- والقيم داخل YAML

أي مبرمج جديد يجب أن يتعامل مع هذا على أنه **مصدر خطر معماري**.

---

## 7.3 `VVMStageRule`
الملف:
- `src/domain/rules/vvm_stage_rule.py`

هذا الملف يحوّل `her_ratio` إلى مرحلة VVM تشغيلية.

### السلوك الحالي
- `>= 1.0 -> D`
- `>= 0.7 -> C`
- `>= 0.4 -> B`
- `>= 0.1 -> A`
- أقل من ذلك -> `NONE`

### لماذا هذا الملف مهم؟
لأن كثيرًا من الحكم العملي النهائي متأثر بهذه العتبات.

### لماذا هو خطير؟
لأن هذه العتبات هي جزء من “العقد غير المعلن” للنظام الحالي.  
إذا غُيّرت دون إعادة ضبط واسعة:
- ستفشل الاختبارات
- ستتغير التقارير
- قد تتغير الأحكام التاريخية

---

## 7.4 `ThermalDegradationEstimator`
الملف:
- `src/domain/services/thermal_degradation_estimator.py`

هذا estimator **advisory** أكثر من كونه تنظيميًا.

يحتوي على:
- `Simplified Q10 calculation`
- تحويل damage إلى `remaining_potency`

هذا الملف مناسب للاستخدام كطبقة تفسير أو تقدير، لكنه ليس أفضل مكان لوضع منطق تنظيمي نهائي.

---

## 7.5 `Q10ThermalCalculator` و `VVMQ10Model`
الملفات:
- `src/domain/calculators/q10_thermal_calculator.py`
- `src/domain/calculators/vvm_q10_model.py`

هذه الملفات توضح بوضوح أن النظام الحالي:
- يستخدم تقريب `Q10`
- وليس محرك `MKT` تنظيميًا كاملًا

يجب على أي مبرمج جديد أن يفهم أن هذه calculators:
- ليست بالضرورة “الحقيقة التنظيمية النهائية”
- لكنها جزء مهم من السلوك الحالي والاختبارات الحالية

---

# 8) مصدر البيانات والثوابت

## 8.1 ملفات الإعدادات الرئيسية
- `config/thresholds.yaml`
- `config/vaccine_library.yaml`

## 8.2 ماذا تحتوي؟
### `thresholds.yaml`
يحتوي على thresholds عامة مثل:
- `remaining_shelf_life_percentage`
- `fridgetag_alarm_enabled`
- `flexible_vvm_allowed`

### `vaccine_library.yaml`
يحتوي على مكتبة لقاحات مركزية تشمل:
- `q10_factor`
- `shelf_life_days`
- `freeze_sensitive`
- `vvm_type`
- `critical_temp_c`
- `critical_hours`
- `source`
- `who_code`
- ملاحظات إضافية

## 8.3 المشكلة الحالية
ليس واضحًا تمامًا أن YAML هو `single source of truth` النهائي، لأن جزءًا مهمًا من المنطق ما يزال معرفًا داخل:
- `src/domain/value_objects/vaccine_specification.py`

لذلك، عند التطوير:
- لا تفترض أن تعديل YAML وحده يكفي
- ولا تفترض أن Python catalogue وحده authoritative
- بل قارن دائمًا بين الاثنين

---

# 9) كيف يتحول الإدخال إلى قرار؟

فيما يلي أبسط صورة لتدفق القرار:

## المسار المنطقي
1. **استقبال القراءات**
2. **تحويلها إلى objects داخلية**
3. **اختيار أو تحديد مواصفة اللقاح**
4. **تحليل التعرض الحراري**
   - HER
   - CCM
   - Freeze / critical heat
5. **تمرير النتائج إلى rules**
6. **توليد decision + reasons**
7. **بناء DTO / response**
8. **تقرير أو حفظ أو إخراج PDF**

## المسار العملي الأقرب
- `EvaluateColdChainSafetyUseCase`
  - يستدعي التحليل
  - يمرر للـ rules
  - يرجع response

- `GenerateDeviceReportUseCase`
  - يجمع timeline
  - يجلب المواصفات
  - يشغّل التقييم التنظيمي/التشغيلي
  - يهيّئ التقرير

---

# 10) الملفات التي يجب أن تحفظها عن ظهر قلب

إذا كنت ستستلم المشروع بجدية، فهذه هي قائمة “الملفات المفصلية”:

## مفصل القرار العلمي
- `src/domain/services/exposure_analysis_service.py`
- `src/domain/value_objects/vaccine_specification.py`
- `src/domain/rules/vvm_stage_rule.py`

## مفصل التكوين
- `src/application/app_composer.py`

## مفصل التشغيل
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
- `src/application/use_cases/generate_device_report_uc.py`
- `src/application/use_cases/import_ft2_bundle_uc.py`

## مفصل الإعدادات
- `config/vaccine_library.yaml`
- `config/thresholds.yaml`

## مفصل الوثائق
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/scientific_models/vvm_q10_model.md`

## مفصل الاختبارات
- `tests/unit/test_a1_exposure_analysis.py`
- `tests/unit/domain/rules/test_vvm_stage_rule.py`

---

# 11) ما الذي يعتبر مستقرًا نسبيًا؟

## مستقر نسبيًا
- البنية الطبقية العامة
- وجود use cases منفصلة
- وجود composition root
- وجود فصل معقول بين domain/application/infrastructure
- وجود اختبارات وحدة لمنطق أساسي
- وجود config + docs + scripts

## غير مستقر أو انتقالي
- الحقيقة العلمية النهائية للثوابت
- مصدر الحقيقة الموحد للقاحات
- العلاقة بين Q10/HER والنموذج التنظيمي المستقبلي
- بعض أجزاء PDF/reporting التي ما زالت تحت التجديد
- بعض القيم والعتبات التي تبدو متغيرة عبر code/YAML/tests

---

# 12) أين توجد المخاطر الفعلية؟

## 12.1 مخاطر علمية
- الخلط بين approximation والنموذج التنظيمي
- وجود عتبات غير موثقة granularly
- احتمال تضارب VVM classes أو shelf-life بين ملفات متعددة

## 12.2 مخاطر معمارية
- duplication بين Python catalogue وYAML
- وجود contracts غير موثقة لكنها مثبتة بالاختبارات
- اعتماد طبقات عليا على مفاتيح dict محددة بدل typed result objects في بعض المواضع

## 12.3 مخاطر تشغيلية
- كسر use case عند تعديل schema
- كسر التقارير عند تغيير decision reasons أو field names
- خلط advisory outputs بالـ regulatory outputs

## 12.4 مخاطر إنتاجية
- licensing/security موجودة في `AppComposer`
- report generation تحت التجديد
- health check الحالي يثبت wiring أساسي لكنه لا يكفي وحده كمعيار جاهزية وطنية

---

# 13) كيف تبدأ التطوير بدون أن تكسر النظام؟

## القاعدة الذهبية
لا تعدّل القلب العلمي مباشرة قبل تثبيت الاختبارات وفهم العقود الحالية.

## خطوات العمل الآمنة
1. اقرأ الاختبارات أولًا
2. حدّد contract الذي تثبته
3. أضف test جديدًا قبل أي refactor كبير
4. إذا كنت ستغيّر منطقًا علميًا:
   - افصل القديم عن الجديد
   - لا تستبدل مباشرة
5. إذا وجدت تكرارًا بين YAML والكود:
   - لا تحذف أحدهما فورًا
   - أثبت أولًا من هو authoritative

## إذا كان التغيير كبيرًا
افعل ذلك بإحدى الطريقتين:
- parallel engine
- adapter compatibility layer

---

# 14) ما الذي يحتاجه النظام قبل الإنتاج الحقيقي؟

لكي يصل المشروع إلى مستوى إنتاجي قوي، يلزم العمل على المحاور التالية:

## 14.1 Source of Truth
تحديد واضح ونهائي:
- هل الحقيقة في YAML؟
- أم في Python catalogue؟
- أم هناك build step يولد أحدهما من الآخر؟

## 14.2 Decision Contract Hardening
تعريف رسمي ومكتوب لـ:
- input schema
- analysis result schema
- decision schema
- reason codes

## 14.3 Scientific Traceability
كل ثابت حرج يجب أن يملك:
- المصدر
- القسم أو الجدول
- سبب استخدامه
- status: verified/unverified

## 14.4 Test Strategy
يلزم توزيع واضح للاختبارات:
- unit
- integration
- architecture
- regression
- golden outputs

## 14.5 Reporting Stability
تثبيت:
- report DTOs
- PDF schema
- text labels
- formatting contracts

## 14.6 Operational Readiness
- logging
- health checks
- configuration validation
- failure handling
- data ingestion robustness

---

# 15) خطة استلام عملية لمبرمج جديد خلال أول 5 أيام

## اليوم 1
- اقرأ:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `SYSTEM_HANDOFF.md`
- افهم بنية الطبقات

## اليوم 2
- اقرأ:
  - `src/application/app_composer.py`
  - `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
  - `src/application/use_cases/generate_device_report_uc.py`

## اليوم 3
- اقرأ:
  - `src/domain/services/exposure_analysis_service.py`
  - `src/domain/value_objects/vaccine_specification.py`
  - `src/domain/rules/vvm_stage_rule.py`

## اليوم 4
- اقرأ:
  - `config/vaccine_library.yaml`
  - `config/thresholds.yaml`
  - `docs/scientific_models/vvm_q10_model.md`

## اليوم 5
- اقرأ الاختبارات:
  - `tests/unit/test_a1_exposure_analysis.py`
  - `tests/unit/domain/rules/test_vvm_stage_rule.py`
- ثم ارسم بنفسك:
  - input → analysis → rules → output

إذا لم تستطع رسم هذا التدفق بوضوح، فأنت لم تستلم النظام بعد.

---

# 16) التوصية النهائية للمطور الجديد

تعامل مع المشروع على أنه يمر بمرحلتين في الوقت نفسه:

## المرحلة الحالية
نظام تشغيلي حقيقي يمكنه:
- قراءة البيانات
- تحليل التعرض
- إصدار مؤشرات وقرارات
- إنتاج تقارير

## المرحلة القادمة
نظام يحتاج:
- توحيد علمي
- توثيق مرجعي أدق
- source-of-truth واضح
- فصل تنظيمي/تشغيلي أقوى
- صلابة أكبر قبل الاعتماد الوطني الكامل

### الخلاصة العملية
إذا أردت أن تطور المشروع بنجاح:
- احترم العقود الحالية
- افصل بين refactor وmodel change
- لا تخلط between operational usefulness and regulatory validity
- اعمل بالتوازي لا بالاستبدال المفاجئ
- اعتبر `ExposureAnalysisService` و`VaccineSpecification` و`VVMStageRule` أهم ثلاث قطع يجب ألا تُعدّلها دون خطة واختبارات

---

# 17) Short System Summary
لمن يريد وصفًا سريعًا جدًا:

> هذا النظام يحوّل قراءات سلسلة التبريد إلى قرار تشغيلي عبر محرك حراري قائم على `Q10/HER`, مع circuit breakers للتجمّد والحرارة الحرجة، وقواعد قرار في طبقة domain، وتنسيق use cases في application، مع adapters وتقارير في infrastructure.  
> بنيته جيدة وقابلة للتوسعة، لكن الوصول للإنتاج الكامل يتطلب توحيد مصدر الحقيقة للثوابت، تقوية التتبع العلمي، وتثبيت العقود بين التحليل والقرار والتقرير.
