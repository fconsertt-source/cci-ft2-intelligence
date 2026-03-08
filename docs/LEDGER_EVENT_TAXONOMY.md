# 📋 Ledger Event Taxonomy — تصنيف أحداث السجل الجنائي

**الإصدار:** v1.0.0
**تاريخ:** 2026-02-27
**الحالة:** ✅ معتمد للإنتاج

---

## 🎯 الهدف

توفير تصنيف موحد وشامل لجميع الأحداث المسجلة في Ledger لضمان:
- ✅ قابلية التدقيق الجنائي (Forensic Audit)
- ✅ سهولة التحليل والإبلاغ
- ✅ اتساق عبر جميع مكونات النظام
- ✅ دعم الترجمة المتعددة اللغات

---

## 📊 فئات الأحداث

| الفئة | الوصف | أمثلة |
|-------|-------|-------|
| **FT2** | عمليات استيراد ومعالجة ملفات FT2 | `FT2_IMPORTED`, `SIGNATURE_VERIFIED` |
| **REPORT** | توليد وتصدير التقارير | `PDF_GENERATED`, `CSV_EXPORTED` |
| **VACCINE** | عمليات اللقاحات وسجل اللقاحات | `VACCINE_ADDED`, `VACCINE_REGISTRY_UPDATED` |
| **UNIT** | وحدات التبريد وقراءات الحرارة | `UNIT_REGISTERED`, `TEMPERATURE_READING` |
| **CYCLE** | إدارة الدورات (Sessions) | `CYCLE_STARTED`, `CYCLE_COMPLETED` |
| **OPERATOR** | جلسات وإجراءات المشغلين | `OPERATOR_SESSION_STARTED`, `OPERATOR_LOGIN` |
| **ERROR** | الأخطاء والاستثناءات | `ERROR_OCCURRED`, `LEDGER_CORRUPTED` |
| **SYSTEM** | أحداث النظام والإعدادات | `SYSTEM_STARTED`, `BACKUP_CREATED` |
| **AUDIT** | التدقيق وفحوصات السلامة | `AUDIT_STARTED`, `HASH_CHAIN_VALID` |
| **LICENSE** | أحداث الترخيص | `LICENSE_ACTIVATED`, `LICENSE_GUARD_CHECK` |

---

## 🔴 أولويات الأحداث

| الأولوية | المعيار | أمثلة |
|----------|---------|-------|
| **HIGH** | أخطاء حرجة، فشل أمني، تلف بيانات | `ERROR_CRITICAL`, `SIGNATURE_INVALID`, `LEDGER_CORRUPTED` |
| **MEDIUM** | أحداث تشغيلية مهمة | `PDF_GENERATED`, `CYCLE_COMPLETED`, `AUDIT_FAILED` |
| **LOW** | أحداث روتينية | `SYSTEM_STARTED`, `LANGUAGE_CHANGED`, `OPERATOR_SESSION_STARTED` |

---

## 📝 هيكل الإدخال (Entry Schema)

```json
{
  "timestamp": "2026-02-27T01:12:51.643000+00:00",
  "event_type": "pdf_generated",
  "event_category": "REPORT",
  "event_priority": "MEDIUM",
  "event_id": "pdf_generated-20260227011251123456",
  "ft2_serial": "130600112764",
  "file_hash": "sha256:abc123...",
  "operator": "admin",
  "cycle_id": "CC-20260227011251",
  "report_type": "OFFICIAL",
  "batch_counts": {"safe": 5, "warning": 1, "discard": 2},
  "previous_hash": "sha256:def456...",
  "current_hash": "sha256:ghi789..."
}
