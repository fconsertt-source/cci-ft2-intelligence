الخطة التنفيذية النهائية — المرحلة A كا مرجع معماري محصن (Hardened Architectural Reference):
الهدف

إنشاء مرجع معماري حي يثبت صحة وصرامة طبقات المشروع (Clean Architecture + Defensive Design)، مع حماية الطبقات بواسطة Guard Layer، وتجهيز المشروع لتطوير آمن مستقبلي دون المخاطرة بالانحراف المعماري.

الركائز التنفيذية
1️⃣ تحصين البيانات — Immutable Data Contracts

إجراء:

تحويل كل الـ DTOs إلى @dataclass(frozen=True) لمنع تعديل البيانات بعد خروجها من Domain.

إنشاء BaseDTO Protocol يضم def to_dict() -> dict لتوحيد واجهة التقارير وSnapshots.

ضمان أحادية الاتجاه Domain → DTO فقط، وأي تحويل عكسي يتم عبر Factories أو Command Objects صريحة.

الهدف: حماية الطبقة الداخلية من أي تسرب أو تعديل غير مقصود من Presentation/Reporting.

2️⃣ طبقات التحقق المزدوج — Dual-Layer Validation

إجراء:

Structural Validation: تحقق من صحة الشكل، النوع، التنسيق (داخل Value Objects أو DTOs).

Business Validation: تحقق من القواعد المنطقية عبر Domain Policies (مثال: RegistrationPolicy).

تسجيل نتائج كلا الطبقتين ضمن تقرير الامتثال لكل عملية.

الهدف: منع تلوث Domain Entities بفحوصات شكلية وضمان توافق البيانات مع سياسات العمل.

3️⃣ نظام الحراسة — The Guard Layer

إجراء:

تغليف كل Use Case بـ context manager: with guard_scope(): ....

توليد تقرير تلقائي (JSON/CSV) يوضح:

DTOs الممررة

الملفات المتأثرة (File Tree)

أي استثناءات تم التعامل معها.

دمج تدوير الملفات (Rotation) لتجنب تراكم ملفات التقارير القديمة.

الهدف: توثيق جميع العمليات بشكل آلي، وضمان الالتزام بالحدود المعمارية، حتى عند فشل أي Use Case.

4️⃣ التوثيق الحي — Living Documentation

إجراء:

توليد مخططات اعتماديات الكود تلقائيًا باستخدام أدوات مثل pydeps أو Mermaid.js.

تضمين package prefix (domain., application.) لتوضيح الحدود بين الطبقات.

تحديث المخططات في README أو GitHub Pages بشكل تلقائي مع كل PR.

الهدف: جعل المرجع المعماري "يشرح نفسه" ويعكس التغييرات مباشرة في الوثائق دون تدخل يدوي.

5️⃣ الانضباط العملياتي — Operational Excellence

إجراء:

إضافة اختبارات No-Entity-Leak وفحوصات Schema للـ Guard Layer.

إدارة الاعتماديات في pyproject.toml (extras: dev, docs) لفصل أدوات التطوير عن كود التشغيل.

توثيق كل السياسات والإجراءات في ADR-0012 لضمان وضوح "لماذا" القيود موجودة.

تنفيذ Rotation وتقسيم التقارير الزمنية لتقليل الضوضاء وتحسين CI/CD.

الهدف: الحفاظ على استقرار المرجع المعماري وتسهيل دمج أي مطور أو فريق جديد دون خرق الطبقات.

خارطة الطريق للمرحلة A
رقم	خطوة	التنفيذ	النتيجة المتوقعة
1	تثبيت DTOs & BaseDTO	frozen dataclasses + واجهة موحدة	Immutable snapshot لكل بيانات خارجة من Domain
2	Validation Layer	Structural + Business validation	عدم تلوث Entities، وتوليد تقارير تحقق
3	Guard Layer	context manager + تقارير JSON/CSV + File Tree	ضمان التزام Use Cases بالحدود المعمارية
4	Living Documentation	توليد Mermaid/pydeps تلقائي	مخططات حية تعكس الكود والاعتماديات
5	Operational Discipline	No-Entity-Leak, Schema Tests, ADR	استقرار معماري، CI/CD محمي، مرجع موثق
مخرجات المرحلة A

مرجع معماري قابل للتنفيذ: كل Use Case وطبقة تم توثيقها وتثبيتها.

تقرير الامتثال الآلي: دليل حي على عدم كسر الحدود المعمارية.

مخططات الاعتماديات الحية: توضح العلاقة بين Domain، Application، Infrastructure، وPresentation.

مرجعية مكتوبة: ADR-0012 + Living Docs تشرح السياسات والقيود.

CI/CD محصن: أي خرق للحدود يؤدي لفشل البناء.

الملاحظات

أي تعديل على المعمارية الحالية يتطلب فتح ADR جديد.

المرحلة A تركز على تثبيت وصيانة المعمارية، لا على إضافة ميزات جديدة خارج السياق.

المرحلة التالية (B) يمكنها التركيز على توسيع الأدوات التشغيلية أو تحسين واجهة الـ CLI مع الحفاظ على نفس Guard Layer.
