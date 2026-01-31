خريطة الطريق المحدثة – Clean Architecture Project (مرحلة البناء التدريجي للواجهات)

تاريخ الإصدار: 2026-01-31
الحالة الحالية: Phase 3 – التحول التدريجي باستخدام DTOs وDI، جميع Guard Scripts ناجحة محليًا وCI

> The Domain layer is unified under `src/domain`.

المرحلة 0 – نقطة التفتيش والتحقق (Verification Gate)

الهدف: التأكد من سلامة الـ Domain قبل أي بناء للواجهات.

الإجراءات العملية:

تشغيل Guard Script على جميع المسارات المحمية:

python3 scripts/check_no_core_entity_imports.py


CI Pipeline يتحقق من:

منع استيراد src.domain.entities في scripts/, src/reporting/, src/presentation/.

نجاح Contract Test (tests/integration/test_no_entity_leak.py).

أي فشل يمنع الدمج (Fail-Fast).

الاستفادة: يحمي المشروع من الانحراف المعماري ويضمن قاعدة صلبة قبل بناء أي واجهات.

المرحلة 1 – Data Contracts / DTOs (Immutable Data)

الهدف: تصميم البيانات المتبادلة بين طبقات Core وPresentation بطريقة آمنة وقابلة للتوسع.

الإجراءات العملية:

تعريف كل DTO باستخدام:

from dataclasses import dataclass

@dataclass(frozen=True)
class CenterDTO:
    id: str
    name: str
    vvm_stage: str
    decision: str


frozen=True لضمان Immutability.

تجنب أي تمرير للكائنات الداخلية المعقدة من Domain Layer.

التأكد من أن كل استخدام للـ DTO يمر عبر Mapper أو Adapter، لا يتم تمرير كائنات Entities مباشرة.

التحقق:

Contract Tests للتأكد من أن Use Cases لا ترجع Entities مباشرة.

المرحلة 2 – Mapping Strategy وAdapters

الهدف: تحويل Entities إلى DTOs بشكل مركزي وآمن.

الإجراءات العملية:

إنشاء Mapping Registry أو مكان مركزي لكل التحويلات:

from src.application.mappers.center_mapper import to_center_dto

DTO = to_center_dto(entity)


استخدام Adapters للربط بين بيانات الـ Infrastructure والـ Application Layer.

معالجة القيم الفارغة (Nulls) بشكل موحد لتجنب أخطاء NoneType في التقارير.

فصل رسائل الخطأ:

الاحتفاظ بـ Exception Codes في Domain.

الرسائل النهائية للمستخدم عبر Message Map في Presentation Layer.

التحقق:

Smoke Tests للتأكد من سلامة التحويلات.

Contract Tests لمراجعة Consistency.

المرحلة 3 – Isolated Legacy Tools

الهدف: فصل الأدوات القديمة خارج المسارات المحمية.

الإجراءات العملية:

نقل simulate_vvm_scenarios.py إلى tools/legacy/.

ترك Shim في scripts/ لتوجيه المطورين وتشغيل Legacy عند الحاجة:

print("NOTICE: simulate_vvm_scenarios has been moved to tools/legacy/")


تحديث Guard Script لاستثناء Legacy بشكل واضح.

PR خاص للعزل (PR#3)، يُدمج بعد PRs الأخرى.

التحقق: تشغيل Guard Script محليًا وCI → لا توجد Import violations.

المرحلة 4 – Presentation Layer / واجهات الاستخدام

الهدف: بناء CLI/Reporting Layer متوافقة مع DTOs وDI.

الإجراءات العملية:

CLI وReporting يستهلكون DTOs فقط.

كل إخراج عبر Logger أو تنسيقات CSV/HTML مأخوذة من DTOs.

Snapshot Testing للتقارير لضمان عدم كسر المخرجات مع تغييرات Domain.

الرسائل للمستخدم عبر Message Map لضمان لغة موحدة.

التحقق:

Contract Tests + Snapshot Tests + Smoke Tests على تقارير CSV/HTML.

المرحلة 5 – CI/CD وBranch Protection

الهدف: ضمان دمج آمن للكود الجديد مع الحفاظ على معايير الجودة.

الإجراءات العملية:

تفعيل Guard + Contract Tests كـ required status checks على branch main.

لا يمكن الدمج إلا إذا اجتاز كل Checks.

استخدام Workflow واحد لكل PR للتحقق:

Guard Script

pytest (Contract Tests + Smoke Tests)

الجدول الزمني الموصى به
المرحلة	المدة	ملاحظات
0 – Verification	1-2 أيام	تشغيل Guard + Contract Tests
1 – DTOs	2-3 أيام	تعريف كل DTOs + Immutability
2 – Mapping/Adapters	3-4 أيام	Mapping Registry + Error Map
3 – Legacy Isolation	1-2 أيام	عزل Legacy Tools + Shim
4 – Presentation Layer	2-3 أيام	CLI/Reporting Layer + Snapshot Tests
5 – CI/CD & Branch Protection	1 يوم	Guard + Tests mandatory before merge
نقاط القوة المحسّنة (Fine-Tuning)

Immutability تمنع Side Effects في Presentation.

Mapping Registry مركزي يضمن اتساق البيانات.

Message Map يضمن لغة موحدة للخطأ.

Guard Script + Contract Tests تمنع أي Architectural Drift.

Snapshot Tests للتقارير تزيد الثقة في النتائج.

العزل التدريجي للأدوات القديمة يقلل المخاطر.

الخلاصة

هذه الخريطة تحول المشروع من مجرد كود إلى منصة قرار طبي بمعايير Clean Architecture وDDD حقيقية. كل خطوة قابلة للتنفيذ، محمية بالاختبارات والحراسة التلقائية، وقابلة للصيانة والتوسع على المدى الطويل.