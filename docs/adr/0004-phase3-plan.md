ADR 0004 — خطة المرحلة 3: تحويل تدريجي باستخدام Composition Root

تاريخ: 2026-01-31
الحالة الحالية: مقبول / Implemented (partial, نحو الإغلاق الكامل بعد الدمج النهائي للـ PRs)

1. السياق

تهدف هذه ADR إلى توثيق القرار والخطوات الخاصة بـ المرحلة 3 من خطة اعتماد الهيكل الجديد للمشروع: تحويل التدفق لمعالجة البيانات ليعتمد DTOs وDI في الطبقات الخارجية، مع ضمان عدم تسريب الكيانات (Entities) خارج طبقة الـ Domain.

2. القرار

إنشاء DTOs أساسية (VaccineDTO, CenterDTO) ومابّرات (application/mappers/*) لتحويل الكيانات الحالية.

إضافة Adapter Layer ضمن src/infrastructure/adapters/ft2_reader_adapter.py لتحويل منطق قراءة البيانات وتحليلها من الملفات إلى DTOs.

توحيد نظام التسجيل (logging) عبر src/infrastructure/logging.py واستخدامه في السكربتات والـ Use Cases.

تعديل scripts/run_ft2_pipeline.py لاستخدام Composition Root / DI Container (src/shared/di_container.py) وتقديم DTOs بدل الكيانات عند استدعاء الـ Use Cases.

عزل الأدوات القديمة:

نقل simulate_vvm_scenarios.py إلى tools/legacy/ كأداة LEGACY.

ترك shim في scripts/ لتوجيه المطورين إلى النسخة المعزولة، ومنع استيراد أي Entities خارج المسارات المسموح بها.

3. العواقب

يسمح بتحول تدريجي دون كسر الوظائف الحالية.

يقلل من تسرب الكيانات إلى الطبقات الخارجية.

يفرض مراجعة دقيقة عند إضافة سكربتات جديدة أو تعديل المسارات الحالية.

يتطلب تحديث السكربتات والواجهات الأخرى لاستخدام DI وDTOs تدريجيًا.

4. التنفيذ الحالي (Implementation Status)

Status: Partial / Accepted

ملخص التنفيذ:

PR	الوصف	الملفات الرئيسية	الهدف
#1	Defense PR — تحويل simple_pipeline.py إلى DTO-only	scripts/simple_pipeline.py + guard + contract test + docs	إثبات إمكانية تنفيذ ADR0004 كنموذج قابل للمراجعة
#2	تحويل مسار الإنتاج	scripts/run_ft2_pipeline.py	إنتاج CenterDTO واستخدام Adapters للربط، دون كسر التشغيل الحالي
#3	عزل أداة Legacy	tools/legacy/simulate_vvm_scenarios.py + shim في scripts/	منع أي تسرب للكيانات من Legacy إلى المسارات المحمية

Guardrails and Tests:

Guard Script: scripts/check_no_core_entity_imports.py يمنع استيراد src.core.entities في المسارات المحمية (scripts/, src/reporting/, src/presentation/).

Workflow CI: .github/workflows/guard.yml لتشغيل الحارس على كل PR.

Contract Test: tests/integration/test_no_entity_leak.py للتأكد من عدم تسرب Entities إلى الطبقات العليا.

النتيجة:
تشغيل الحارس محليًا وضمن CI: ✅ No forbidden imports found
خطوط الإنتاج المحوّلة تعمل مع DTO-only، Legacy معزولة، جميع PRs جاهزة للدمج.

5. عناصر العمل المتبقية / Next Steps

دمج PRs #1–3 بشكل تسلسلي:

PR#1 — simple_pipeline

PR#2 — run_ft2_pipeline

PR#3 — simulate_vvm_scenarios (Legacy isolation)

تحديث ADR0004 بإضافة روابط PR النهائية وحالة التنفيذ النهائية: Implemented.

تحديث docs/ProjectState.md لتوثيق اكتمال المرحلة 3.

إضافة اختبارات عقدية إضافية (Contract Tests) للتحقق من أن جميع Use Cases لا تُخرج Entities خارج طبقة Domain.

مراجعة وإزالة أي أدوات Legacy إضافية عند الحاجة، أو تحويلها تدريجيًا إلى DTOs.

6. ملاحظات

هذه المرحلة تعتمد على تغييرات تدريجية وآمنة بدل إعادة كتابة ضخمة (“big-bang”), لضمان تتبع دقيق للأدلة.

Guard وContract Test يشكلان خط الدفاع ضد الانتهاكات المعمارية أثناء تنفيذ التحويل التدريجي.

كل PR يقدم نموذجًا قابلًا للمراجعة (defensible), مع ربط واضح بين ADR والملفات والتعديلات.