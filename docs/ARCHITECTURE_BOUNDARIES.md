# حدود معمارية — CCI-FT2 Intelligence

**النسخة:** 1.0  
**التاريخ:** 2026-04-03  
**الحالة:** ✅ معتمد

## المسموح (Allowed)

| من | إلى | الحالة |
|----|-----|--------|
| Domain | Domain | ✅ |
| Application | Domain | ✅ |
| Infrastructure | Domain (Ports فقط) | ✅ |
| Scripts | أي طبقة | ✅ (Composition Root) |
| Tests | أي طبقة | ✅ |

## الممنوع (Forbidden)

| من | إلى | الحالة |
|----|-----|--------|
| Domain | Application/Infrastructure | ❌ |
| Application | Infrastructure | ❌ |
| Infrastructure | Application (Use Cases) | ❌ |

## الاستثناءات

1. `scripts/run_ft2_pipeline.py` — Composition Root ✅
2. `tests/` — اختبارات تحتاج وصول كامل ✅
