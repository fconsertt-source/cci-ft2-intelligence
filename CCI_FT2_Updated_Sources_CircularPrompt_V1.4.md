# CCI-FT2 Intelligence – Source Verification & Circular AI Prompt

**البند** | **التفصيل**
--- | ---
**رقم الوثيقة** | CCI-REF-2026-04-V1.4
**تاريخ التحديث** | 9 أبريل 2026
**يُكمل** | CCI-REF-2026-04-V1.3
**المحتوى الجديد** | ① تحقق 9 مصادر WHO/PQS/UNICEF/CDC جديدة<br>② تصحيحات Fridge-tag 2E + Remaining Shelf-Life + Flexible VVM<br>③ Circular Prompt v1.4<br>④ Action Items محدثة
**الحالة** | ✅ موثق من المصادر الأولية (جميع PDFs السابقة + 9 ملفات جديدة)

---

## الجزء الأول: التحقق من المصادر – نتائج مراجعة الملفات الجديدة (9 وثائق)

**الملفات المراجعة:**
- 63-making-use-of-vaccie-vvm-polio.pdf (WHO 2000) → Flexible “Fast Chain”
- WHO-PQS-E006-TR07-VP 3_0.pdf + Fridge-tag 2E Manual → Electronic CCM
- trs1025-annex8.pdf → Remaining Shelf-Life عند التسليم
- General-Procurement-Guidelines-Cold-Chain.pdf (UNICEF 2020)
- 9789240015432-eng.pdf → Guidelines on International Packaging & Shipping (الطبعة السادسة)
- نموذجان AEFI عربيان (NCDC)

**نتائج التحقق الرئيسية:**

| البند                  | الملف                          | التفصيل الجديد / التصحيح                          | الحكم          |
|------------------------|--------------------------------|---------------------------------------------------|----------------|
| Flexible VVM           | Polio VVM Guide 2000           | “Fast Chain” = استخدام VVM فقط في حملات شلل الأطفال | ✅ مؤكد        |
| Electronic CCM         | PQS E006-TR07 + Fridge-tag 2E  | Fridge-tag 2E (internal sensor + alarm + LOC)    | ✅ مؤكد        |
| Remaining Shelf-Life   | TRS 1025 Annex 8               | ≥50% عند التسليم (موصى به)                       | ✅ مؤكد        |
| Packaging & Shipping   | 6th Edition Guidelines         | تعليمات التعبئة والشحن الدولي محدثة              | ✅ مؤكد        |

---

## الجزء الثاني: التصحيحات الفعلية (V1.4)

### B6 – تصحيحات جديدة

| اللقاح / القاعدة       | الحقل                     | القيمة الصحيحة                          | المصدر                          |
|-------------------------|---------------------------|------------------------------------------|---------------------------------|
| GENERAL                 | remaining_shelf_life_min  | ≥50% عند التسليم                         | TRS 1025 Annex 8               |
| CCM (Electronic)        | device_type               | Fridge-tag 2E (internal sensor)          | PQS E006-TR07 + Manual         |
| POLIO / VVM             | flexible_chain            | مُسموح “Fast Chain”                      | Polio VVM Guide 2000           |

### B7 – إضافات thresholds.yaml
- `remaining_shelf_life_percentage: 50`
- `fridgetag_alarm_enabled: true`
- `flexible_vvm_allowed: true`

---

## الجزء الثالث: الـ Prompt الدائري المحدث (v1.4)

```markdown
=============================================================
CCI-FT2 INTELLIGENCE – CIRCULAR AI PROMPT v1.4
(يُحقن في كل جلسة – 9 أبريل 2026)
=============================================================

أنت مساعد ذكي متخصص في نظام CCI-FT2 Intelligence.

**STEP-1:** تحديد المصدر المطلوب (src/ → config/ → docs/ → VACCINE_CATALOGUE)

**STEP-2:** التحقق من التطابق (RULE-A إلى RULE-P)

**RULE-M (جديد):** Fridge-tag 2E يجب أن يطابق PQS E006-TR07 (internal sensor + alarm + LOC)
**RULE-N (جديد):** Remaining Shelf-Life ≥50% عند التسليم (TRS 1025 Annex 8)
**RULE-O (جديد):** Flexible VVM (“Fast Chain”) مسموح فقط في حملات شلل الأطفال
**RULE-P (جديد):** Temperature Excursion → ربط بـ AEFI reporting

**STEP-3:** صياغة الإجابة مع علامة المصدر  
`[SRC: مسار_الملف:رقم_السطر] النص`

**STEP-4:** إشعار الفجوات + GAP-ALERT

**STEP-5:** التحذيرات الإلزامية (دائمة)
⚠️ يجب التحقق من منشورات WHO/PQS قبل الإنتاج
⚠️ NoOpLicenseGuard = خطر أمني في الإنتاج
=============================================================