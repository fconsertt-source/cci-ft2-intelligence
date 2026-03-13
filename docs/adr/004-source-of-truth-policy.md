# ADR 004: Source of Truth Policy للكيانات النطاقية

## Status
Accepted — 2025-03-03

## Context
خلال Phase 3، اكتشفنا تكرار كيانات مثل `FT2Entry` في طبقات متعددة، مما سبب:
- تضارب استيراد
- انجراف عقود
- صعوبة صيانة

## Decision
نعتمد السياسة التالية:

### 1. الكيانات النطاقية الحرجة
يجب أن تُعرّف **مرة واحدة فقط** في `src/domain/`:

| الكيان | المسار الصحيح |
|--------|--------------|
| `FT2Entry` | `src/domain/entities/ft2_entry.py` |
| `VaccinationCenter` | `src/domain/entities/vaccination_center.py` |
| `DeviceReportDTO` | `src/application/dtos/device_report_dto.py` |
| `GenerateDeviceReportRequest` | `src/application/use_cases/requests.py` |

### 2. الاستيراد الموحّد
جميع الطبقات تستورد من المصدر الصحيح:
```python
# ✅ صحيح
from src.domain.entities.ft2_entry import FT2Entry

# ❌ خاطئ
from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Entry
```

### 3. استثناءات مسموحة
- `tests/`: يمكن أن يكون لها test doubles
- Aliases مع `DeprecationWarning`: للانتقال التدريجي
- DTOs في `application/`: مسموح لأنها ليست domain entities

## Consequences
### إيجابية
✅ مصدر واحد للحقيقة
✅ منع انجراف العقود
✅ سهولة الصيانة

### سلبية
⚠️ حاجة لمراجعة عند إضافة كيانات جديدة
⚠️ pre-commit hook قد يبطئ commit قليلاً

## Compliance
- [ ] `scripts/detect_duplicate_entities.py` ينفذ هذه السياسة
- [ ] `tests/contracts/test_architecture_contracts.py` يختبرها
- [ ] `.pre-commit-config.yaml` يمنع الانتهاكات
- [ ] CI gate يفشل عند الانتهاك

## Related
- ADR 001: Clean Architecture
- ADR 002: PDF Generator Strategy
- Phase 3: Time & Mathematical Integrity
