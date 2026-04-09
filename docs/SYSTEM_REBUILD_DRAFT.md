# مسودة النظام الكاملة لإعادة البناء

## 1. ملخص عام

**اسم النظام:** الحارس الرقمي لسلسلة التبريد (CCI-FT2 Intelligence)

**الهدف:** بناء نظام معمارية نظيفة يضمن سلامة اللقاحات أثناء النقل والتخزين، عن طريق تحليل قراءة درجات الحرارة من أجهزة FT2، وحساب مؤشرات حرارية علمية، وإصدار قرارات دقيقة وغير قابلة للتلاعب.

**مخرجات الدراسة:** هذا الملف يجمع من الوثائق الرئيسية والكود الفعلي جميع المعلومات اللازمة لإعادة بناء النظام.

---

## 2. الفكرة الأساسية والغاية

### 2.1 الفكرة

النظام ليس مجرد "مولد تقارير"؛ إنه **حارس رقمي** يصدر حكمًا نهائيًا على سلامة اللقاح بناءً على:
- بيانات درجة الحرارة الخام من أجهزة FT2.
- حسابات علمية لـ HER و CCM.
- قواعد صارمة تمنع التعديل أو التوزيع "الإيجابي" للنتائج.

### 2.2 الغاية

- حماية سلامة اللقاحات.
- التأكد من أن أي خرق حراري يؤدي إلى قرار رفض واضح.
- منع أي تعديل للقراءات الأصلية أو التجاوز عن القواعد العلمية.
- دعم المستويات التشغيلية من القراءة وحتى التقارير والإنتاج.

### 2.3 المبادئ الأساسية

1. **التدهور أحادي الاتجاه (Unidirectional Decay)**
   - اللقاح يتدهور؛ لا يُعاد تجديده.
   - المؤشرات التراكمية مثل HER/CCM يجب أن تزيد فقط.

2. **قدسية البيانات الخام**
   - لا تنقية، لا تعديل، لا حذف.
   - الـ Infrastructure يقرأ الواقع فقط.

3. **عزل الزمن**
   - الاعتماد على الفواصل الزمنية (`duration_minutes`) لا على الطابع الزمني المطلق.

4. **قاعدة أضعف حلقة**
   - مركز سليم يُقاس بأخطر جهاز فيه.

5. **فصل كامل بين الطبقات**
   - Domain لا يستورد Infrastructure.
   - Presentation لا يحتوي منطق قرار.

---

## 3. الهيكل العام للنظام

النظام مصمم وفق Clean Architecture.

### 3.1 الطبقات

- `src/domain`: القواعد العلمية، الكيانات، القيم.
- `src/application`: حالات الاستخدام، الـ Ports، الـ DTOs، الخدمات التطبيقية.
- `src/infrastructure`: قراءة الملفات، تخزين البيانات، إنشاء التقارير، الأمان.
- `src/presentation`: CLI وواجهات التشغيل.
- `src/application/app_composer.py`: جذر التركيب ومسؤول بناء الاعتماديات.

### 3.2 تدفق الاعتماديات

`Presentation → Application → Domain ← Infrastructure`

- Presentation يستدعي Use Cases.
- Use Cases يعتمد على واجهات (Ports) من Application.
- Infrastructure ينفذ هذه الواجهات.
- Domain يحتوي على القواعد ولا يتعرف إلى implementers.

### 3.3 ملفات التكوين الأساسية

- `config/base.yaml`
- `config/production.yaml`
- `config/system_config.yaml`
- `config/thresholds.yaml`
- `config/vaccine_library.yaml`

### 3.4 الوثائق المعمارية الرئيسية

- `README.md`
- `docs/Clean_Architecture_Project.md`
- `docs/ARCHITECTURE.md`
- `docs/foundational_charter.md`
- `docs/ARCHITECTURE_BOUNDARIES.md`
- `docs/phase-a-hardened-architecture-plan.md`
- `docs/DEPLOYMENT.md`
- `docs/RUNBOOK.md`

---

## 4. قراءة البيانات ومعالجة الـ FT2

### 4.1 مسار البيانات

1. ملفات FT2 الخام (مثلاً في `data/input_ft2/`).
2. تحويل إلى تنسيق وسيط JSON بواسطة `src/presentation/cli/cli.py -> import_data`.
3. قراءة وتحليل القراءات في `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`.
4. توليد تقرير جهاز/مركز.

### 4.2 الكود الفعلي لقراءة السجلات

- `EvaluateColdChainSafetyUseCase` يقرأ الطلب في `DomainCenterContext.from_request()`.
- يتم فرز القراءات حسب تمثيل الطابع الزمني كسلسلة قبل تحويلها.
- يدعم تنسيقات طابع زمني متعددة:
  - ISO مع `Z`
  - `%Y-%m-%d %H:%M:%S`
  - `%Y-%m-%d %H:%M`
- يتم تسجيل تحذيرات في حال وجود طابع زمني غير قابل للتحويل.

### 4.3 بناء الـ TemperatureEntry

لكل قراءة:
- `temperature`
- `timestamp`
- `duration_minutes` بين القراءة الحالية واللاحقة.
- `device_id` إن وجد.

هذا يعني أن النظام يعتمد على الفترات الزمنية بين القيم وليس على قيم الطابع الزمني المطلقة.

### 4.4 ملاحظات غير موثقة في الكود

- إذا كانت قائمة القراءات فارغة، يرجع القرار `NO_DATA`.
- يتم إنشاء آخر قراءة بمدة `0.0` دقيقة.
- تتم عملية الفرز الأولى قبل تحويل الطوابع، ما قد يؤدي إلى ترتيب غير صحيح إذا تغير تنسيق السلسلة.

---

## 5. الحسابات الحرارية والقرارات

### 5.1 ExposureAnalysisService

المسؤوليات:
- تفعيل الـ `Circuit Breakers` الحرجة.
- حساب HER ratio باستخدام نموذج `Q10`.
- حساب مؤشر CCM وفق `WHO/PQS/E06/IN02.1`.
- تحديد درجات حرارة قصوى ودنيا.

### 5.2 قواعد CCM

- `+10°C` تعتبر العتبة العليا.
- `+34°C` تعتبر حالة حرجة.
- إذا حافظ الجهاز على `>34°C` لمدة ساعتين فإن القرار يتحول إلى `DISCARD`.

### 5.3 قواعد HER

- يتم استخدام `Q10` و `shelf_life_hours` من مواصفة اللقاح.
- إذا لم تُمرَّر المواصفة، يستعمل النظام `VACCINE_CATALOGUE["GENERAL"]` أو مواصفة موقعة مبدئيًا من `VACCINE_CATALOGUE`.
- يحتوي الكود على fallback لمواصفة مخصصة إذا مرَّر constructor قيمًا قديمة (`reference_temp`, `q10_value`, `shelf_life_hours`).

### 5.4 Circuit Breakers وقرارات التحذير

النظام يفصل بين القرار الفوري والتحليل المتدرج:
- `Circuit Breakers` ترجع سببًا فوريًا مثل `FREEZE_EXCURSION` أو `CRITICAL_HEAT_34C`.
- هذا لا يجعل القرار النهائي، لكنه يقدّم إحصاءً مهمًا للـ `RulesEngine`.

### 5.5 RulesEngine

- `src/domain/services/rules_engine.py` يحتوي على مجموعة قواعد مرتبة:
  - `ExpiryRule`
  - `VVMStageRule`
  - `ThawRule`
  - `FreezeRule`
  - `HeatCriticalRule`
  - `HeatDurationRule`
  - `TemperatureWarningRule`
  - `DefaultRule`
- كل قاعدة تُقيّم على التوالي، وفي أول نتيجة تقرر الحالة النهائية.
- `apply_rules(center, extra_stats, enable_heat_duration)` يحسب إحصاءات المركز ويُحدّث `center.decision` و `center.decision_reasons`.

### 5.6 JudgmentEngine

- `src/domain/services/judgment_engine.py` لا يصدر القرارات القانونية، بل ينتج شرحًا بشريًا للقرار.
- ينتج:
  - `risk_level`
  - `risk_icon`
  - `narrative`
  - `recommendations`
  - `confidence`
  - `requires_human_review`
- القواعد الداخلية تشمل:
  - أي قرار `DISCARD` يحتاج مراجعة بشرية.
  - HER مرتفع أو CCM `D` يخفض الثقة.
  - `freeze_detected` أو `critical_heat` يرفع مستوى المخاطرة.

### 5.7 ملاحظات في توليد التقارير

- `src/infrastructure/reporting/pdf_report_generator.py` يولّد تقارير PDF.
- يعتمد على `reportlab` ويخطط لإنشاء PDF من جداول ونص.
- إذا فشل استيراد `reportlab`، فإنه يفرّط إلى ملف نصي (`.txt`) كنسخة احتياطية.
- بعد إنشاء التقرير، يحسب تجزئة SHA-256 لحماية سلامة المخرجات.

---

## 6. ملاحظات غير موثقة في الوثائق

### 6.1 اختلاف بين الوثائق والكود

- `pyproject.toml` يعرّف سكربت `ft2-cli = "src.cli:main"` ولكن الملف الموجود فعليًا هو `src/presentation/cli/cli.py`.
- وثائق النشر تشير إلى `python -m src.presentation.cli.main` بينما الكود يحتوي على `src/presentation/cli/cli.py` مع أمر `if __name__ == "__main__"`.

### 6.2 حالات غير مكتملة في CLI

- الأمران `evaluate` و `report` في CLI يعرضان رسائل مجردة ولا ينفذان تحليلًا فعليًا.
- `generate_all_device_reports` يحتوي على رسالة `DEVICE_REPORTS_NOT_YET_IMPLEMENTED`.

### 6.3 اعتمادات ترخيص داخلية

- `src/application/app_composer.py` يستخدم `_NoOpLicenseGuard` افتراضيًا.
- هذا يعني أن خط ترخيص الإنتاج الحقيقي موجود في النظام لكنه غير مفعل في تركيب `GenerateDeviceReportUseCase`.

### 6.4 سلوك `ExposureAnalysisService`

- إذا كان `enable_supply_date` مفعلًا، يتم تصفية القراءات الأقدم من تاريخ التوريد.
- هذا السلوك غير موثق في ملفات المتطلبات الرئيسية لكنه مدعوم في الكود.

### 6.5 الاعتماد على الـ fallback في مواصفات اللقاح

- الكود يسمح باستخدام مواصفة "CUSTOM" إذا لم تتوفر مواصفات اللقاح.
- مصدر المواصفة الافتراضية هو `VACCINE_CATALOGUE["GENERAL"]`.

### 6.6 حماية التقرير

- `PDFReportGenerator` يحسب SHA-256 لكل تقرير.
- هذا سلوك أمان مهم لحفظ النزاهة لكنه غير مذكور في وثائق الاستخدام العامة.

### 6.7 قواعد بنية المعمارية

- يوجد سكربتات حماية معمارية في `scripts/` مثل:
  - `check_no_core_entity_imports.py`
  - `check_layer_dependencies.py`
  - `check_src_root_clean.py`
- هذه السكربتات تؤكد الالتزام بمبدأ Clean Architecture.

---

## 7. التشغيل والنشر

### 7.1 متطلبات أساسية

- Python 3.10+ (الوثائق تشير إلى 3.12+)
- Docker & Docker Compose
- PostgreSQL 13+
- 4GB RAM، 10GB قرص

### 7.2 متغيرات البيئة

- `CCI_ENV` (production/development)
- `CCI_DATA_ROOT`
- `CCI_LOG_LEVEL`
- `CCI_ENABLE_SUPPLY_DATE` (feature flag)
- `CCI_ENABLE_HEAT_DURATION` (feature flag)

### 7.3 خطوات النشر المتوقعة

1. استنساخ المستودع.
2. نسخ `config/base.yaml` إلى `config/production.yaml` وتعديله.
3. تشغيل `docker-compose up -d`.
4. تشغيل CLI أو خدمة العرض.

### 7.4 تشغيل يدوي

- `python -m src.presentation.cli.cli` (غير موثق صراحة لكنه هو الملف الموجود).
- قد يكون الأمر الرسمي في الوثائق غير متوافق.

### 7.5 دليل التشغيل والصيانة

من `docs/RUNBOOK.md`:
- فحص الصحة
- فشل التقرير
- مشاكل الأداء
- فحص السجلات والمساحة
- النسخ الاحتياطي الأسبوعي
- فحص الأمان الشهري

---

## 8. خطة إعادة البناء من جديد

### 8.1 ثوابت يجب الحفاظ عليها

- فصل طبقات Clean Architecture.
- الالتزام بقواعد `Domain` العلمية ولا تسمح للبنية التحتية بالتأثير عليها.
- حساب HER/CCM والـ Circuit Breakers في طبقة Domain أو خدمة تحليل Domain.
- تخزين المخرجات بتنسيق قابل للتدقيق مع تجزئة رقمية.
- إبقاء واجهة السطر بسيطة وخالية من المنطق التحليلي.

### 8.2 منصات إعادة البناء المقترحة

1. **بناء النموذج الأولي**
   - `src/domain` بالكيانات والقواعد.
   - `src/application` بحالات الاستخدام والواجهات.
   - `src/infrastructure` للقارئ والتقارير.
   - `src/presentation` للعملية التشغيلية.

2. **تنفيذ التحليل الحراري**
   - دعم بيانات FT2 الخام.
   - استخراج `duration_minutes` بين القراءات.
   - حساب `her_ratio` و `ccm_index` و `freeze_detected` و `critical_heat`.

3. **إنشاء المحرك القائم على القواعد**
   - تطبيق `RulesEngine` كقائمة من قواعد متسلسلة.
   - إعادة استخدام `decision_reasons` لإرسال سبب القرار.

4. **إضافة طبقة شرح القرار**
   - `JudgmentEngine` لإنتاج سرد وتوصيات.
   - يجب أن تكون هذه الطبقة منفصلة عن القرار نفسه.

5. **توليد التقرير**
   - PDF مع fallback إلى نص.
   - تجزئة SHA-256 لكل ملف.
   - دعم لثلاث لغات على الأقل (العربية والانجليزية مذكورة ضمن النص).

6. **اختبارات وحماية معماريّة**
   - تنفيذ سكربتات تحقق من حدود الاستيراد.
   - صيانة `health_check` لبناء الاعتماديات.
   - إنشاء اختبارات وحدة للـ Domain وقواعد التحليل.

### 8.3 اعتبارات إضافية

- إصلاح عدم التوافق في `pyproject.toml` و`CLI` entrypoint.
- توثيق الفلاتر الخاصة بتاريخ التوريد (`enable_supply_date`).
- توثيق استخدام `enable_heat_duration` كميزة قابلة للتشغيل.
- توثيق أن `AppComposer` يستخدم `NoOpLicenseGuard` لأغراض الاختبار.

---

## 9. ملخص الملفات الرئيسية لبناء مرجع جديد

- `README.md`
- `docs/foundational_charter.md`
- `docs/ARCHITECTURE.md`
- `docs/Clean_Architecture_Project.md`
- `docs/DEPLOYMENT.md`
- `docs/RUNBOOK.md`
- `src/application/app_composer.py`
- `src/presentation/cli/cli.py`
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
- `src/domain/services/exposure_analysis_service.py`
- `src/domain/services/rules_engine.py`
- `src/domain/services/judgment_engine.py`
- `src/infrastructure/reporting/pdf_report_generator.py`
- `scripts/check_no_core_entity_imports.py`
- `scripts/check_layer_dependencies.py`

---

## 10. توصيات سريعة

- ابدأ من الوثائق المذكورة أعلاه، لكن اعتمد أكثر على الكود في `src/domain` و`src/application`.
- صحح أولًا عدم التوافق بين `pyproject.toml` وملفات CLI الحقيقية.
- حافظ على مبدأ `لا تعديل للبيانات الخام` كقاعدة أولى.
- اجعل أي ميزة تشغيلية جديدة تخضع لقاعدة `Feature Flag` مثل `CCI_ENABLE_SUPPLY_DATE`.
- وثّق كل سلوك غير بديهي أو fallback في الكود عند إعادة البناء.

---

*هذه المسودة صُممت لتكون مرجعًا متكاملاً لإعادة بناء النظام من جديد، مع تضمين المعلومات التي ظهرت فقط في الكود ولم تُوثق سابقًا.*
