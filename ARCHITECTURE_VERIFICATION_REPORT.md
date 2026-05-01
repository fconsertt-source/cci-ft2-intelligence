# تقرير التحقق المعماري لخطة الإصلاح المصححة

**المشروع:** `cci-ft2-intelligence-clean`  
**تاريخ الفحص:** 2026-04-29  
**نطاق الفحص:** الكود الفعلي داخل `src/`, `scripts/`, `tests/`  
**قيد التنفيذ:** لم يتم تعديل أي كود إنتاجي. هذا الملف هو المخرج الوحيد.

---

## 1. الخلاصة التنفيذية

الحكم المؤسسي صحيح جزئياً، لكنه غير مكتمل.

الصحيح في الحكم:

- لا يوجد `import pandas` داخل `src/domain/`.
- يوجد انتهاك واضح لـ `pandas` داخل `src/application/services/incremental_processor.py`.
- `RuntimeCenterRegistry` معرف فعلاً ككلاس داخلي داخل `run_pipeline()` في `scripts/run_ft2_pipeline.py`.
- `ColdChainContinuityValidator` مستورد داخل `run_ft2_pipeline.py` ولا يستخدم بعد الاستيراد.
- `device_map` يبنى داخل `run_ft2_pipeline.py` ولا يستخدم خارج كتلة البناء نفسها.
- `EvaluateColdChainSafetyUseCase` ينشئ `ExposureAnalysisService`, و`ScientificReferenceService`, و`JudgmentEngine` داخلياً.

الخاطئ أو الناقص في الحكم:

- المشكلة في Application ليست `pandas` فقط. يوجد خرق مباشر أوسع لقاعدة الاعتماد على الخارج:
  - `src/application/services/incremental_processor.py` يستورد `SessionRegistry`, و`ParquetStorageRepository`, و`SessionNotFoundError` من Infrastructure.
  - `src/application/app_composer.py` يستورد عدة تطبيقات Infrastructure مباشرة.
  - `src/application/use_cases/generate_device_report_uc.py` يستورد `ConfigLoader` من Infrastructure.
- عدد استخدامات `datetime.now()` داخل `run_ft2_pipeline.py` المرتبطة بالتشغيل ليس 3 بل 4:
  - `run_id`
  - `report_id`
  - `processed_at`
  - `metrics.finished_at`
- `ExposureAnalysisService` نظيف من `pandas` و`datetime.now()`، لكن ليس خالياً تماماً من المخاطر: عند تفعيل `enable_supply_date` مع تاريخ naive سيستخدم `timezone.utc` دون استيراد `timezone`.
- `ScientificReferenceService` داخل Domain يقرأ YAML من `config/scientific_constants.yaml` مباشرة، وهذا يخالف الفصل الصارم إذا اعتبرنا Domain طبقة نقية لا تقرأ ملفات ولا تعتمد على صيغة تخزين.
- `DeviceRegistry` داخل Domain يدير ملفات JSON مباشرة ويكتب إلى القرص، وهو خرق معماري أكبر غير مذكور في التقرير الأصلي.

الحكم النهائي: **خطة التنفيذ المصححة قابلة للتنفيذ جزئياً، لكنها لا تكفي وحدها للوصول إلى فصل طبقات صارم. أضعف نقطة هي حدود Application، لا `pandas` وحدها.**

---

## 2. طرق التحقق الثلاث

### الطريقة الأولى: فحص أمامي لخريطة الاستيرادات

بدأ الفحص من الطبقات إلى التبعيات.

أوامر التحقق المستخدمة:

```bash
rg -n "import pandas|from pandas|pd\\." src scripts tests
rg -n "src\\.infrastructure|src\\.presentation|pandas|pyarrow|pd\\." src/application src/domain
```

نتائج مهمة من الكود:

- `src/application/services/incremental_processor.py:4` يحتوي `import pandas as pd`.
- `src/application/services/incremental_processor.py:6-8` يستورد من Infrastructure مباشرة.
- `src/application/app_composer.py:18-23` يستورد adapters/repositories/security من Infrastructure.
- `src/application/app_composer.py:106` يستورد `PDFGenerator` من Infrastructure داخل الدالة.
- `src/application/use_cases/generate_device_report_uc.py:18` يستورد `ConfigLoader` من Infrastructure.
- لا يوجد `pandas` داخل `src/domain/`.

استنتاج الطريقة الأولى:

الحكم صحيح في أن `pandas` غير موجودة في Domain، وصحيح أن `incremental_processor.py` خرق واضح، لكنه ناقص لأن خرق Application أوسع من مكتبة Pandas.

### الطريقة الثانية: فحص عكسي للاستخدامات والكود الميت

بدأ الفحص من الادعاءات نفسها: هل هذه الرموز مستخدمة فعلاً أم هي ضجيج؟

أوامر التحقق المستخدمة:

```bash
rg -n "ColdChainContinuityValidator|device_map|datetime\\.now|RuntimeCenterRegistry|EvaluateColdChainSafetyUseCase|ExposureAnalysisService\\(|JudgmentEngine\\(|ScientificReferenceService\\(" src scripts tests
```

نتائج مهمة من الكود:

- `scripts/run_ft2_pipeline.py:231` يعرف `RuntimeCenterRegistry` داخل `run_pipeline()`.
- `scripts/run_ft2_pipeline.py:269` ينشئ `RuntimeCenterRegistry(centers)`.
- `scripts/run_ft2_pipeline.py:280` يستورد `ColdChainContinuityValidator`.
- لا يوجد استخدام لاحق لـ `ColdChainContinuityValidator` داخل السكربت.
- `scripts/run_ft2_pipeline.py:289-293` يبني `device_map`.
- لا يوجد استخدام فعلي لـ `device_map` بعد البناء.
- `scripts/run_ft2_pipeline.py:366` ينشئ `EvaluateColdChainSafetyUseCase()` دون حقن.
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py:134` ينشئ `ExposureAnalysisService()` مباشرة.
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py:152` ينشئ `ScientificReferenceService()` مباشرة.
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py:183` ينشئ `JudgmentEngine()` مباشرة.

استنتاج الطريقة الثانية:

الحذف الفوري للاستيراد الميت وكتلة `device_map` آمن من حيث السلوك المرصود. ونقل `RuntimeCenterRegistry` إلى ملف مستقل ممكن بلا تغيير عقد `ICenterRegistry` لأن الكلاس الداخلي يطبق الدوال المطلوبة فعلياً.

### الطريقة الثالثة: فحص العقود التنفيذية والاختبارات ككود

تمت محاولة تشغيل الاختبارات المعمارية والوحدوية، لكن بيئة التشغيل لا تحتوي `pytest`.

الأوامر والنتائج:

```bash
pytest ... -q
# /bin/bash: pytest: command not found

python3 -m pytest ... -q
# /usr/bin/python3: No module named pytest

python3 -m py_compile scripts/run_ft2_pipeline.py \
  src/application/services/incremental_processor.py \
  src/application/use_cases/evaluate_cold_chain_safety_use_case.py \
  src/infrastructure/storage/parquet_repository.py
# نجح بلا أخطاء
```

ولأن `pytest` غير متاح، تم قراءة الاختبارات المعمارية نفسها كعقود:

- `tests/architecture/test_application_layer.py:6-7` يحدد `src/application` كطبقة لا يجب أن تستورد `infrastructure`.
- `tests/architecture/test_application_layer.py:25-33` يفشل إذا استوردت Application أي `infrastructure`.
- `tests/architecture/test_domain_purity.py:9-10` يمنع Domain من استيراد `application`, و`infrastructure`, و`presentation`.
- `tests/architecture/test_dependency_isolation.py:10-32` يوثق أن بعض Use Cases يجب أن تتطلب حقن تبعيات.

استنتاج الطريقة الثالثة:

لو كان `pytest` متاحاً، فمن المتوقع أن يفشل `test_application_does_not_import_infrastructure` بسبب الاستيرادات الحالية في Application. لذلك أضعف نتيجة في التحقق هي: **حدود Application مخترقة بأكثر من موضع، ولا يكفي علاج Pandas وحدها.**

---

## 3. تقييم خطة التنفيذ المصححة بنداً بنداً

### 3.1 التصحيح الفوري: حذف الكود الميت

الحكم: **قابل للتنفيذ بالكامل وبمخاطرة منخفضة جداً.**

الدليل:

- `ColdChainContinuityValidator` مستورد في `scripts/run_ft2_pipeline.py:280` فقط داخل السكربت ولا يستخدم.
- `device_map` يبنى في `scripts/run_ft2_pipeline.py:289-293` ولا يقرأ بعد ذلك.

الملاحظة:

النسخة الاحتياطية `scripts/run_ft2_pipeline.py.bak.20260403_0929` تحتوي استخداماً قديماً لـ `device_map`، لكن الملف النشط لا يحتوي هذا الاستخدام. لذلك الحذف آمن في الملف النشط فقط.

### 3.2 البروتوكول A: نقل `RuntimeCenterRegistry`

الحكم: **قابل للتنفيذ مع تعديل بسيط في الخطة.**

الدليل:

- `ICenterRegistry` يطلب:
  - `get_all_device_ids()`
  - `get_center_id_for_device(device_id)`
  - `get_registered_center_count()`
- الكلاس الداخلي الحالي يطبق هذه الدوال في `scripts/run_ft2_pipeline.py:253-263`.
- الدالتان الإضافيتان `get_center_by_device_id()` و`all_centers()` ليستا جزءاً من الواجهة، لكن السكربت يستخدم `get_center_by_device_id()` في `scripts/run_ft2_pipeline.py:324`.

التعديل المطلوب:

ملف `src/infrastructure/registry/runtime_center_registry.py` المقترح مناسب، لكن يجب الانتباه إلى أن `get_center_by_device_id()` ليست جزءاً من `ICenterRegistry`. إما:

- إضافتها إلى واجهة منفصلة موجهة للـ Pipeline، أو
- إبقاؤها كدالة Infrastructure إضافية مع إدراك أن السكربت يعتمد على concrete class لا على الواجهة فقط في تلك النقطة.

### 3.3 البروتوكول B: حقن تبعيات `EvaluateColdChainSafetyUseCase`

الحكم: **قابل للتنفيذ، لكن الخطة المقترحة ستكسر اختبارات حالية إذا جعلت التبعيات إجبارية فوراً.**

الدليل:

- الاختبارات الحالية تنشئ `EvaluateColdChainSafetyUseCase()` بلا معاملات:
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py:15`
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py:48`
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py:89`
  - `tests/unit/test_phase2_smoke.py:24`
  - `tests/unit/test_phase2_smoke.py:46`

الخطة الآمنة:

- المرحلة الأولى: إضافة `__init__` بتبعيات اختيارية مع defaults للحفاظ على التوافق.
- المرحلة الثانية: تحديث نقطة التجميع في `run_ft2_pipeline.py` لاستخدام الحقن الصريح.
- المرحلة الثالثة: تحديث الاختبارات لاستخدام mocks حيث يلزم.
- المرحلة الرابعة: بعد استقرار الاختبارات، يمكن جعل بعض التبعيات إجبارية إذا كان هذا هو معيار المشروع.

ملاحظة مهمة:

`ScientificReferenceService` ليس مجرد خدمة حسابية نقية بالكامل لأنه يقرأ إعدادات YAML مباشرة داخل Domain. حقنه في Use Case يحسن الاختبار، لكنه لا يحل وحده مشكلة القراءة من الملفات داخل Domain.

### 3.4 البروتوكول C: إخراج Pandas من `incremental_processor.py`

الحكم: **قابل للتنفيذ جزئياً، لكنه يحتاج إعادة تصميم أوسع من المقترح.**

الدليل:

`src/application/services/incremental_processor.py` لا يستخدم Pandas كسطر زائد فقط، بل يعتمد عليها في:

- قراءة CSV: `pd.read_csv(csv_path)` في السطر 63.
- ترتيب وإزالة تكرار: `sort_values(...).drop_duplicates(...)` في السطر 64.
- تحويل بيانات التخزين إلى DataFrame: `_to_dataframe()` في السطور 11-19.
- إنشاء DataFrame فارغ في السطر 73.
- الدمج: `pd.concat(...)` في السطر 77.
- حساب `time_range` من الأعمدة في السطر 91.

كما أن الملف نفسه يستورد Infrastructure مباشرة:

- `SessionRegistry` في السطر 6.
- `ParquetStorageRepository` في السطر 7.
- `SessionNotFoundError` في السطر 8.

لذلك نقل Pandas إلى `ParquetStorageRepository` فقط لا يكفي. يجب تعريف حدود Port واضحة.

### 3.5 البروتوكول D: توحيد `datetime.now()` في Pipeline

الحكم: **قابل للتنفيذ، لكن يجب تصحيح العدد والنطاق.**

الاستخدامات داخل `scripts/run_ft2_pipeline.py`:

- `run_id` في السطر 216.
- `report_id` في السطر 421.
- `processed_at` في السطر 469.
- `metrics.finished_at` في السطر 528.

الخطة المقترحة باستخدام `run_timestamp` جيدة، لكن يجب استخدامها في المواضع الأربعة، أو الفصل بين:

- `run_started_at`
- `run_finished_at`

إذا كان مطلوباً قياس مدة التشغيل بدقة، فلا يجب جعل `metrics.finished_at` مساوياً لبداية التشغيل. أما إذا كان الهدف determinism في الاختبارات فقط، فالأفضل حقن `Clock` أو دالة `now_provider`.

---

## 4. الخطة الجديدة المبنية على أضعف نتيجة

أضعف نتيجة في التحقق هي: **Application Layer لا تلتزم بقاعدة الاعتماد على Ports فقط.**

لذلك الخطة الجديدة تبدأ من حدود الطبقات قبل تفاصيل Pandas.

### المرحلة 0: تثبيت خط الأساس

الأهداف:

- تثبيت تقرير الحالة الحالي.
- عدم تنفيذ تغييرات مختلطة دفعة واحدة.
- تشغيل الاختبارات بعد تثبيت بيئة `pytest`.

أوامر مطلوبة بعد تجهيز البيئة:

```bash
python3 -m pip install -r requirements-test.txt
python3 -m pytest tests/architecture tests/contracts -q
python3 -m pytest tests/unit/application/use_cases tests/unit/infrastructure/test_pandas_cold_chain_analyzer.py -q
```

### المرحلة 1: إصلاح الكود الميت و`RuntimeCenterRegistry`

التغييرات:

- حذف استيراد `ColdChainContinuityValidator` من `scripts/run_ft2_pipeline.py`.
- حذف كتلة `device_map`.
- إنشاء `src/infrastructure/registry/runtime_center_registry.py`.
- استيراد `RuntimeCenterRegistry` في `run_ft2_pipeline.py`.
- إضافة اختبار وحدة لـ `RuntimeCenterRegistry`.

سبب البدء بها:

هذه تغييرات منخفضة المخاطر وتعطي تحسناً فورياً في قابلية الاختبار.

### المرحلة 2: نقل نقطة التجميع خارج Application

التغييرات:

- التعامل مع `src/application/app_composer.py` كخرق معماري.
- نقله أو إعادة إنشائه في طبقة تركيب خارجية مثل:
  - `src/shared/app_composer.py` إذا كان هذا هو النمط المعتمد في المشروع.
  - أو `src/infrastructure/composition/app_composer.py`.
  - أو `scripts/`/Presentation إذا كانت نقطة تشغيل فقط.

المبرر:

Application يجب أن تعرف Ports وUse Cases، لا أن تبني `DeviceDataRepository`, و`LicenseGuard`, و`PDFGenerator` من Infrastructure.

### المرحلة 3: تصميم Ports للمعالجة التزايدية

بدلاً من أن يعتمد `IncrementalPipelineProcessor` على `SessionRegistry` و`ParquetStorageRepository` مباشرة، تقترح الخطة:

- `src/application/ports/session_registry_port.py`
  - `is_new_data(device_id, file_timestamp) -> bool`
  - `mark_processed(device_id, last_timestamp, filename, readings_count) -> None`
- `src/application/ports/session_storage_port.py`
  - يمكن استخدام عقد شبيه بـ `StorageProtocol` الحالي.
  - يجب ألا يسرّب `SessionNotFoundError` من Infrastructure إلى Application.
- `src/application/ports/session_ingestion_port.py`
  - `merge_file(device_id, csv_path, existing_rows) -> MergeResult`
  - أو `read_normalized_rows(csv_path) -> Iterable[dict]`.

الخيار الأفضل للبيانات الكبيرة:

- اجعل الدمج الذي يحتاج Pandas أو PyArrow داخل Infrastructure كخدمة:
  - `src/infrastructure/storage/pandas_session_merger.py`
  - أو `src/infrastructure/ingestion/csv_session_ingestor.py`
- Application تستدعي Port وتتعامل مع `MergeResult` فقط.

النتيجة المطلوبة:

`src/application/services/incremental_processor.py` يجب أن يخلو من:

- `import pandas`
- `from src.infrastructure...`
- استثناءات Infrastructure
- تفاصيل Parquet

### المرحلة 4: حقن تبعيات `EvaluateColdChainSafetyUseCase`

التغييرات:

- إضافة constructor اختياري:
  - `exposure_service`
  - `judgment_engine`
  - `scientific_service`
  - `config`
- إبقاء القيم الافتراضية مؤقتاً حتى لا تنكسر الاختبارات القديمة.
- تعديل `run_ft2_pipeline.py` ليكون نقطة التجميع الصريحة لهذه التبعيات.

صيغة آمنة مبدئياً:

```python
class EvaluateColdChainSafetyUseCase:
    def __init__(
        self,
        exposure_service=None,
        judgment_engine=None,
        scientific_service=None,
        config=None,
    ):
        self._exposure = exposure_service or ExposureAnalysisService()
        self._judgment = judgment_engine or JudgmentEngine()
        self._scientific = scientific_service or ScientificReferenceService()
        self._config = config or get_config()
```

هذه ليست النهاية المثالية، لكنها انتقال آمن لا يكسر الاختبارات الحالية فوراً.

### المرحلة 5: إصلاح الوقت والـ Clock

التغييرات:

- إضافة `run_timestamp` أو `clock` إلى `run_pipeline()`.
- استخدامه في:
  - `run_id`
  - `report_id`
  - `processed_at`
- اتخاذ قرار صريح حول `metrics.finished_at`:
  - إما وقت نهاية حقيقي من `clock.now()`.
  - أو نفس `run_timestamp` إذا كان الهدف reproducibility فقط.

### المرحلة 6: معالجة ملاحظات Domain الأعمق

هذه ليست شرطاً لإنجاح الخطة المصححة فوراً، لكنها مهمة للفصل الصارم:

- نقل قراءة YAML من `ScientificReferenceService` إلى Port/Repository.
- نقل التخزين JSON من `DeviceRegistry` إلى Infrastructure أو حقن repository/port.
- إصلاح `ExposureAnalysisService` باستيراد `timezone` أو توحيد معالجة الوقت خارج الخدمة.

---

## 5. التطبيق الافتراضي للخطة على الكود

تمت محاكاة الخطة على الكود الحالي دون تعديل الملفات.

### بعد المرحلة 1

المتوقع:

- `run_ft2_pipeline.py` يصبح أقصر.
- لا يتغير مسار المعالجة لأن `device_map` غير مستخدم.
- `ColdChainContinuityValidator` يبقى في Domain ومغطى باختباراته، لكنه لا يستورد عبثاً في Pipeline.
- اختبار جديد لـ `RuntimeCenterRegistry` يصبح ممكناً دون تشغيل Pipeline كامل.

الخطر:

- منخفض جداً.

### بعد المرحلة 2

المتوقع:

- تقل مخالفات `tests/architecture/test_application_layer.py`.
- قد تحتاج import paths في الاختبارات أو نقاط الدخول إلى تحديث.

الخطر:

- متوسط، لأن `AppComposer` قد يكون مستخدماً من presentation أو tests.

### بعد المرحلة 3

المتوقع:

- يختفي `pandas` من Application.
- تختفي استيرادات Infrastructure من `incremental_processor.py`.
- تصبح المعالجة التزايدية قابلة للاختبار بمخازن وهمية وقراء CSV وهميين.

الخطر:

- متوسط إلى عالٍ إذا لم يتم الحفاظ على نفس دلالات الدمج الحالية:
  - الترتيب حسب `timestamp`
  - الاحتفاظ بآخر قراءة عند تكرار `timestamp`
  - حساب `new_readings`
  - حساب `total_readings`
  - حساب `time_range`
  - سلوك `force`

### بعد المرحلة 4

المتوقع:

- يصبح `EvaluateColdChainSafetyUseCase` قابلاً لاختبار الوحدة الحقيقي.
- يمكن حقن mocks بدلاً من حساب Q10/Judgment كامل في كل اختبار.
- يجب أن تبقى الاختبارات الحالية ناجحة إذا استخدمت التبعيات الاختيارية.

الخطر:

- منخفض إلى متوسط.

### بعد المرحلة 5

المتوقع:

- يصبح Pipeline قابلاً لإعادة التشغيل deterministically في الاختبارات.
- تقل فروق أسماء التقارير ووقت التسجيل بين تشغيل وآخر.

الخطر:

- منخفض، بشرط عدم الخلط بين وقت بداية التشغيل ووقت نهايته.

---

## 6. الصحيح والخاطئ في تكوين النظام الحالي

### الصحيح حالياً

- Domain لا يحتوي `pandas`.
- توجد DTOs وPorts واضحة في أجزاء كثيرة من Application.
- `ParquetStorageRepository` يعرض بيانات خام `dict` ولا يسرّب DataFrame في واجهة `read_session/write_session`.
- `RuntimeCenterRegistry` الحالي يطبق دوال `ICenterRegistry` المطلوبة، حتى لو كان في المكان الخطأ.
- Use Case الرئيسي يعمل حالياً بتكوين بسيط، وهذا يفسر نجاح الاختبارات القديمة التي تنشئه بلا معاملات.
- توجد اختبارات معمارية في `tests/architecture` تعبر عن نية فصل الطبقات.

### الخاطئ حالياً

- Application تستورد Infrastructure مباشرة في عدة مواضع.
- `incremental_processor.py` يجمع منطق application orchestration مع Pandas وParquet وSessionRegistry.
- `EvaluateColdChainSafetyUseCase` يخفي تبعيات مهمة داخله.
- `run_ft2_pipeline.py` يحتوي كلاس داخلي واستخدامات وقت غير قابلة للحقن.
- بعض مكونات Domain تتعامل مع ملفات وإعدادات مباشرة، خاصة `ScientificReferenceService` و`DeviceRegistry`.
- الاختبارات المعمارية غير قابلة للتشغيل في البيئة الحالية لأن `pytest` غير مثبت.

### بعد تطبيق الحلول المقترحة افتراضياً

المنتج النهائي سيكون أقوى إذا تحققت الشروط التالية:

- Application تعتمد على Ports فقط عند التعامل مع التخزين، CSV، Parquet، التراخيص، والتقارير.
- Infrastructure توفر implementations لهذه Ports.
- Composition Root يبني النظام من الخارج.
- Use Cases تقبل تبعياتها بالحقن.
- Pipeline لا يحتوي كلاس داخلي ولا وقت نظام مبعثر.
- اختبارات architecture تصبح gate حقيقي في CI.

النتيجة المتوقعة:

- اختبارات الوحدة تصبح أسهل وأسرع.
- تغيير التخزين من Parquet إلى غيره لا يمس Application.
- يمكن اختبار قرارات اللقاحات دون قراءة ملفات أو إنشاء خدمات حقيقية.
- تقل مخاطر regression في المعالجة التزايدية.

---

## 7. ملاحظات إضافية غير مذكورة في التقرير الأصلي

### 7.1 `ExposureAnalysisService` يحتوي خطأ محتمل في `timezone`

في `src/domain/services/exposure_analysis_service.py`:

- السطر 19 يستورد `datetime` فقط.
- السطور 101-111 تستخدم `timezone.utc`.

إذا كان `enable_supply_date=True` ومر تاريخ `supply_date` دون timezone، سيحدث `NameError` لأن `timezone` غير مستورد.

### 7.2 `ScientificReferenceService` داخل Domain يقرأ ملفات YAML

في `src/domain/services/scientific_reference_service.py`:

- السطر 7: `import yaml`
- السطر 34: `Path("config/scientific_constants.yaml")`
- السطر 41: فتح الملف
- السطر 42: `yaml.safe_load`

هذا يخالف الفصل الصارم لأن Domain أصبح يعرف مسار ملف وصيغة تخزين.

### 7.3 `DeviceRegistry` داخل Domain يكتب ويقرأ JSON

في `src/domain/services/device_registry.py`:

- السطر 14: `import json`
- السطر 17: `Path`
- السطر 91: إنشاء مجلدات
- السطور 356-393: قراءة وكتابة ملفات JSON

هذا مكون Infrastructure موجود داخل Domain بالمعنى المعماري، حتى لو كان تحت اسم service.

### 7.4 `generate_device_report_uc.py` يخلط Use Case مع ConfigLoader

في `src/application/use_cases/generate_device_report_uc.py:18` يوجد استيراد مباشر من:

```python
from src.infrastructure.utils.config_loader import ConfigLoader
```

ويستخدم في السطور 91 و174. هذا يجب أن يتحول إلى إعدادات محقونة أو Port.

### 7.5 `app_composer.py` موجود داخل Application

`src/application/app_composer.py` يعمل كنقطة تركيب، لكنه يستورد Infrastructure. في Clean Architecture، نقطة التركيب تكون خارج Application غالباً.

---

## 8. القرار النهائي حول خطة التنفيذ المصححة

| البند | القرار | السبب |
|---|---|---|
| حذف `ColdChainContinuityValidator` من Pipeline | موافق بالكامل | استيراد بلا استخدام في الملف النشط |
| حذف `device_map` | موافق بالكامل | يبنى ولا يقرأ بعد البناء |
| نقل `RuntimeCenterRegistry` | موافق مع ضبط الواجهة | الكلاس يطبق العقد، لكن لديه دالة إضافية يستخدمها Pipeline |
| حقن تبعيات `EvaluateColdChainSafetyUseCase` | موافق تدريجياً | يجب الحفاظ على التوافق مع اختبارات تنشئه بلا معاملات |
| إخراج Pandas من `incremental_processor.py` | موافق لكن الخطة ناقصة | يجب إزالة Infrastructure imports أيضاً، لا Pandas فقط |
| توحيد `datetime.now()` | موافق مع تصحيح العدد | توجد 4 مواضع في Pipeline لا 3 |

---

## 9. توصية العمل لمهندس جديد

ابدأ من الاختبارات المعمارية، لا من Pandas.

الترتيب العملي المقترح:

1. جهز بيئة الاختبار وثبت `pytest`.
2. شغل اختبارات `tests/architecture` وخذها كخط أساس.
3. نفذ الحذف الفوري ونقل `RuntimeCenterRegistry`.
4. انقل أو أعد تموضع `AppComposer` خارج Application.
5. صمم Ports للمعالجة التزايدية قبل نقل Pandas.
6. أضف حقن تبعيات `EvaluateColdChainSafetyUseCase` بشكل متوافق.
7. عالج `datetime.now()` عبر `clock` أو `run_timestamp`.
8. بعد استقرار ذلك، افتح ملف Domain purity الأعمق: YAML/JSON داخل Domain.

الخطة الأصلية كانت جيدة كبداية، لكن نقطة النجاح الحقيقية ليست "إزالة Pandas" فقط؛ النجاح هو جعل اتجاه الاعتماد دائماً من الخارج إلى الداخل، وكل ما هو تخزين أو ملف أو مكتبة تقنية يبقى خلف Port واضح.
