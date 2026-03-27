# ADR 0003 — نتائج فحص الالتزام بالميثاق (المرحلة 2)

تاريخ: 2026-01-31

الحالة: مسجّل — يحتاج عمل متابعة

## الخلفية

تم تنفيذ فحوصات الالتزام بالميثاق وفقًا لمرحلة 2. الهدف هو التحقق من أن الطبقات تفصل بشكل صحيح (Domain, Application, Infrastructure, Presentation, Shared)، وأن العمليات التالية متوافقة: استخدام DTOs في العرض، وجود الاستثناءات في `src/domain/exceptions`, وجود ADRs، ووجود Composition Root.

## النتائج الأساسية

1. **إعادة التصدير المؤقتة (Temporary re-exports)**
   - تم إنشاء re-exports تحت `src/infrastructure/parsers` و `src/infrastructure/validators`، و `src/domain` facade لتحاشي كسر الواردات الفوري.
   - هذا الإجراء موثق ويجب اعتباره مؤقتًا حتى الانتهاء من Refactor تدريجي. (انظر ADR 0001)

2. **انحرافات في Presentation**
   - `scripts/run_ft2_pipeline.py` يستورد ويستخدم مباشرة `FT2Entry`, `FT2Parser`, `FT2Validator`, و `VaccinationCenter` (من `src.core.entities`).
   - هذا ينتهك بند الميثاق: لا يجب أن تستخدم طبقة العرض Entities مباشرة؛ يجب أن تعمل بالـ DTOs فقط.

3. **Exceptions و Logging**
   - لا توجد حالياً تعريفات استثناءات متفرقة في `src/domain/exceptions` قبل التغيير؛ تم إضافتها كجزء من المرحلة السابقة.
   - تسجيل الأحداث (`logging`) يتم في الملفات المختلفة (بما فيها `scripts/run_ft2_pipeline.py`) ويكتب إلى `pipeline.log`. يُنصح بتوحيد واجهة التسجيل عبر `infrastructure/logging` أو `src/shared`.

4. **Composition Root**
   - `src/main.py` فارغ؛ لا يوجد Composition Root مركزي قائم في الوقت الحالي.
   - تم إضافة `src/shared/di_container.py` كخطوة أولية لتوحيد حقن الاعتماديات.

## قرارات وتوصيات العمل

- لا يُنصح ببدء Refactor شامل قبل معالجة انحرافات العرض: يجب أولًا إنشاء DTOs ومطابقات في `src/application/mappers`, ثم تعديل `scripts/` وواجهات العرض لاستهلاك DTOs فقط.
- اقتراح خطوات متتابعة:
  1. إنشاء DTOs ناقصة إن وجدت وإضافتها إلى `src/application/dtos/`.
  2. نقل أو تكييف `scripts/run_ft2_pipeline.py` ليستخدم Composition Root (`src/shared/di_container`) للحصول على Reader/UseCase.
  3. استبدال الحوادث المباشرة للـ Entities في العرض بمخرجات DTO عبر المappers.
  4. توحيد آلية التسجيل عبر `src/infrastructure/logging.py` أو `src/shared/logging_adapter.py`.

## مرفقات

- الإجرائيات التي نُفذت: إنشاء `src/shared/di_container.py`, واجهات re-export، ملف ADR هذا.
