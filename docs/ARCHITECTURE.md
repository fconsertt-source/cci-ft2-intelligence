# Clean Architecture — CCI-FT2 Intelligence

## نظرة عامة

يتبع هذا المشروع مبادئ Clean Architecture لضمان فصل المسؤوليات، سهولة الصيانة، والاختبارية. الهيكل مبني على طبقات متحدة المستوى مع تدفق اعتماديات من الخارج إلى الداخل.

## الطبقات الأساسية

### 1. Domain Layer (النواة)
- **المسؤولية**: قواعد العمل النقية، entities، value objects، enums.
- **محتويات**:
  - `entities/`: VaccinationCenter, EquipmentRecord, etc.
  - `value_objects/`: TemperatureEntry, VaccineSpec, etc.
  - `enums/`: VVMStage, SafetyStatus, etc.
  - `rules/`: BaseRule, VVMStageRule, HeatExposureRule.
  - `services/`: RegulatoryDecisionService.
- **قيود**: لا استيراد من Application أو Infrastructure.

### 2. Application Layer
- **المسؤولية**: تنسيق Use Cases، Ports، DTOs.
- **محتويات**:
  - `ports/`: IReportGenerator, IRepository.
  - `use_cases/`: GenerateDeviceReportUC, EvaluateColdChainSafetyUC.
  - `dtos/`: DeviceReportDTO, CenterReportDTO (frozen=True مع validation).
  - `services/`: JudgmentEngine لتنسيق القواعد.
- **قيود**: يعتمد فقط على Domain.

### 3. Infrastructure Layer
- **المسؤولية**: تنفيذ تقني (PDF, DB, Files).
- **محتويات**:
  - `adapters/`: FT2ReaderAdapter, JSONRepositoryAdapter.
  - `repositories/`: DeviceRepository, VaccineRepository.
  - `reporting/`: PDFReportGenerator, formatters.
- **قيود**: ينفذ Ports من Application.

### 4. Presentation Layer
- **المسؤولية**: واجهات المستخدم (CLI, GUI).
- **محتويات**: cli.py, gui_main.py.

### 5. Composition Root
- **المسؤولية**: تجميع الاعتماديات (DI Container).
- **محتويات**:
  - `di_container.py`: Simple DI with auto-registration.
  - `app_composer.py`: تسجيل الاعتماديات.

## تدفق الاعتماديات

```
Presentation → Application → Domain ← Infrastructure
     ↓            ↓            ↑            ↑
   CLI/GUI    Use Cases    Entities    Adapters
                    ↓            ↑
               DTOs ← Ports → Implementations
```

## مبادئ مطبقة

- **Dependency Rule**: الاعتماديات تتجه للداخل.
- **Dependency Inversion**: Domain يحدد Interfaces، Infrastructure ينفذ.
- **Single Responsibility**: كل طبقة مسؤولية واحدة.
- **Immutability**: DTOs frozen مع validation.
- **Type Safety**: أنواع محددة بدلاً من dict.

## أمثلة على التدفق

### توليد تقرير جهاز
1. `run_ft2_pipeline.py` (Composition Root) يستدعي `GenerateDeviceReportUC`.
2. `GenerateDeviceReportUC` يستخدم `IReportGenerator` (Port).
3. `PDFReportGenerator` (Infrastructure) ينفذ الـ Port.
4. البيانات تأتي من Domain عبر DTOs.

### تقييم السلامة
1. `EvaluateColdChainSafetyUC` يستدعي `ExposureAnalysisService` (Domain).
2. `JudgmentEngine` يطبق `BaseRule` instances.
3. القرار يُرجع عبر DTO.

## الاختبارات

- **Unit**: Domain rules, DTOs validation.
- **Integration**: Use Cases مع Ports.
- **Architecture**: عزل الطبقات (AST analysis).

## التحسينات المطبقة

- **BaseRule**: Abstract class مع safe_evaluate لتجنب exceptions.
- **DI Container**: Auto-registration لتقليل manual wiring.
- **DTO Validation**: __post_init__ للتحقق من البيانات.
- **JudgmentEngine**: Orchestrates rules safely.