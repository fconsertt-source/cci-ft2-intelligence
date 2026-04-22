# مقترح معماري للواجهات — CCI-FT2 Intelligence

## 1. ملخص تنفيذي

النظام الحالي يتكون من:
- **CLI** (Typer) — 4 أوامر: `health_check`, `import_data`, `generate_device_report`, `generate_all_device_reports`
- **GUI** (Tkinter) — نافذة واحدة `GuardianGUI` (1200×800) مع 6 أزرار، معظمها يعرض "قريبًا"
- **PDF Reports** — ReportLab + matplotlib (عربي/إنجليزي) مع جداول بيانات وتوقيعات

المقترح يحول هذا إلى **واجهة ويب تفاعلية حديثة** (React + TypeScript) مع الحفاظ على طبقة Python كـ **Backend API**.

---

## 2. المعمية المقترحة

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │Dashboard │ │DeviceCard│ │VVMIndicator│ │DecisionBadge│ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │TempChart │ │ImportPanel│ │ReportViewer│ │AuditLog   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │
│                      │                                   │
│              Custom Hooks Layer                          │
│  ┌──────────────┐ ┌────────────┐ ┌─────────────────┐   │
│  │useDeviceData │ │useLanguage │ │useSafetyEval     │   │
│  └──────────────┘ └────────────┘ └─────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST + SSE
┌──────────────────────┴──────────────────────────────────┐
│                Python Backend (FastAPI)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API Routes (REST)                                  │ │
│  │  /api/devices  /api/centers  /api/reports           │ │
│  │  /api/import   /api/verify   /api/ledger            │ │
│  └────────────────────────────────────────────────────┘ │
│                      │                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Use Cases (existing — no changes needed)            │ │
│  │  GenerateDeviceReportUseCase                        │ │
│  │  EvaluateColdChainSafetyUseCase                     │ │
│  │  ImportFT2BundleUseCase                             │ │
│  │  GeneratePDFReportUseCase                           │ │
│  └────────────────────────────────────────────────────┘ │
│                      │                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Domain Layer (existing — pure business logic)       │ │
│  │  Entities · Value Objects · Calculators · Engines    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 3. خريطة المكوّنات المقترحة

### 3.1 المكوّنات الأساسية (Core Components)

| المكوّن | الوصف | الحقول المعروضة من النظام |
|---------|-------|--------------------------|
| **Dashboard** | لوحة التحكم الرئيسية | ملخص المراكز، الأجهزة، قرارات السلامة |
| **DeviceCard** | بطاقة جهاز فردي | `device_id`, `decision`, `vvm_stage`, `her_ratio`, `ccm_index`, `max_temp`, `min_temp`, `circuit_breaker` |
| **VVMIndicator** | مؤشر مرحلة VVM | `vvm_stage` (NONE→A→B→C→D) مع ألوان وARIA labels |
| **DecisionBadge** | شارة القرار | `SAFE`/`PARTIAL`/`DISCARD`/`NO_DATA` مع أيقونات |
| **TemperatureChart** | رسم بياني مصغّر | `readings[]` → `{timestamp, temperature, duration}` |
| **ImportPanel** | لوحة استيراد ملفات FT2 | اختيار TXT+PDF، عرض `FileClassificationResult` |
| **ReportViewer** | عارض التقارير | عرض `DeviceReportDTO` أو PDF embedded |
| **AuditLogViewer** | عارض سجل التدقيق | `LedgerEntry[]` من `LedgerWriterPort` |
| **CenterSummary** | ملخص مركز تطعيم | `CenterReportDTO`: إجمالي الأجهزة، المقبولة، المرفوضة |

### 3.2 مكوّنات مساعدة (Utility Components)

| المكوّن | الوصف |
|---------|-------|
| **LoadingSkeleton** | هيكل تحميل متحرك |
| **ErrorBoundary** | التقاط الأخطاء وعرض رسالة |
| **EmptyState** | حالة فارغة مع إجراء |
| **LanguageSwitcher** | تبديل عربي/إنجليزي |
| **ThemeProvider** | تبديل سمة فاتح/داكن/عالي التباين |

---

## 4. تصميم الخصائص (Props Design)

### 4.1 TypeScript Types (مستمدة من DTOs الموجودة)

```typescript
// ── Enums (من domain/enums/) ──
type SafetyStatus = "SAFE" | "PARTIAL" | "DISCARD" | "NO_DATA";
type VVMStage = "NONE" | "A" | "B" | "C" | "D";
type ReportDecision =
  | "ACCEPTED"
  | "REJECTED_HEAT_C"
  | "REJECTED_FREEZE"
  | "REJECTED_EXPIRED"
  | "REJECTED_THAW"
  | "PARTIAL"
  | "SAFE"
  | "UNKNOWN";
type AlertLevel = "GREEN" | "YELLOW" | "RED";
type ExcursionType = "HEAT" | "FREEZE";

// ── Value Objects (من domain/value_objects/) ──
interface TemperatureReading {
  device_id: string;
  value: number;           // °C
  recorded_at: string;     // ISO 8601
  duration_hours?: number;
}

interface ThermalExcursionDTO {
  device_id: string;
  excursion_type: ExcursionType;
  duration_minutes: number;
  max_temperature?: number;
  min_temperature?: number;
  timestamp?: string;
  impact_level: string;
  aefi_report_recommended: boolean;
}

// ── DTOs (من application/dtos/) ──
interface DeviceReportDTO {
  device_id: string;
  center_id: string;
  center_name: string;
  temperature_ranges: { min: number; max: number };
  decision: ReportDecision;
  vvm_stage: VVMStage;
  alert_level: AlertLevel;
  stability_budget_consumed_pct: number;  // 0–100
  thaw_remaining_hours: number;
  aefi_reporting_required: boolean;
  decision_reasons: string[];
  readings: Array<{
    timestamp: string;
    temperature: number;
    duration: number;
  }>;
  stats: {
    total_records: number;
    excursions_count: number;
    vaccine_type: string;
    operator: string;
    cycle_id: string;
  };
  excursions: ThermalExcursionDTO[];
  vaccine_type: string;
  generated_at: string;
  ledger_hash: string;
}

interface CenterReportDTO {
  center_id: string;
  center_name: string;
  total_devices: number;
  safe_devices: number;
  rejected_devices: number;
  partial_devices: number;
  devices: DeviceReportDTO[];
  summary_stats: Record<string, unknown>;
  recommendations: string[];
  generated_at: string;
}

interface EvaluateColdChainSafetyResponse {
  center_id: string;
  decision: string;
  vvm_stage: string;
  alert_level: string | null;
  stability_budget_consumed_pct: number;
  thaw_remaining_hours: number | null;
  category_display: string | null;
  decision_reasons: string[];
  has_freeze: boolean;
  has_who_heat_exposure: boolean;
  has_heat_duration_breach: boolean;
  her_ratio: number;
  ccm_index: string;    // "0" | "A" | "B" | "C" | "ABC" | "D"
  judgment_risk: string;
  judgment_icon: string;
  confidence: number;
  requires_review: boolean;
  her_percentage: number;
  judgment_narrative: string;
}
```

### 4.2 Component Props Interfaces

#### Dashboard

```typescript
interface DashboardProps {
  /** قائمة تقارير الأجهزة من CenterReportDTO.devices */
  devices: DeviceReportDTO[];
  /** ملخص المركز */
  centerSummary?: CenterReportDTO;
  /** حالة التحميل */
  loading: boolean;
  /** خطأ إن وجد */
  error: Error | null;
  /** عند النقر على جهاز */
  onDeviceSelect: (deviceId: string) => void;
  /** عند طلب استيراد */
  onImport: () => void;
  /** عند طلب توليد تقرير */
  onGenerateReport: (deviceId?: string) => void;
  /** عند طلب تحديث البيانات */
  onRefresh: () => void;
  /** معرّف اللغة الحالية */
  lang: "ar" | "en";
}
```

#### DeviceCard

```typescript
interface DeviceCardProps {
  /** تقرير الجهاز */
  report: DeviceReportDTO;
  /** موسّع أم لا */
  expanded: boolean;
  /** عند التبديل */
  onToggle: () => void;
  /** عند طلب تقرير PDF */
  onGeneratePDF: (deviceId: string) => void;
  /** تصنيف مخصّص */
  className?: string;
}
```

#### VVMIndicator

```typescript
interface VVMIndicatorProps {
  /** المرحلة */
  stage: VVMStage;
  /** حجم العرض */
  size?: "sm" | "md" | "lg";
  /** إظهار التسمية */
  showLabel?: boolean;
  /** معرّف اللغة */
  lang: "ar" | "en";
  /** معرّف فريد لـ aria */
  id?: string;
}

// Color mapping (من VVMStage.get_color() في النظام):
// NONE  → #808080 (رمادي)
// A     → #4CAF50 (أخضر)
// B     → #FFC107 (أصفر)
// C     → #FF9800 (برتقالي)
// D     → #F44336 (أحمر داكن)
```

#### DecisionBadge

```typescript
interface DecisionBadgeProps {
  /** القرار */
  decision: SafetyStatus | ReportDecision;
  /** نمط العرض */
  variant?: "pill" | "icon-label" | "full";
  /** إظهار الوصف */
  showDescription?: boolean;
  /** معرّف اللغة */
  lang: "ar" | "en";
}

// Mapping:
// SAFE    → 🟢 أخضر    → "مقبول" / "Acceptable"
// PARTIAL → 🟡 أصفر   → "تحت المراقبة" / "Partial"
// DISCARD → 🔴 أحمر   → "مرفوض" / "Discard"
// NO_DATA → ⚪ رمادي  → "لا بيانات" / "No Data"
```

#### TemperatureChart

```typescript
interface TemperatureChartProps {
  /** القراءات الحرارية */
  readings: Array<{
    timestamp: string;
    temperature: number;
  }>;
  /** الحدود */
  thresholds?: {
    min: number;   // 2°C افتراضيًا
    max: number;   // 8°C افتراضيًا
  };
  /** ارتفاع الرسم */
  height?: number;
  /** إظهار عتبات التجمد والحرارة الحرجة */
  showCriticalLines?: boolean;
  /** معرّف اللغة */
  lang: "ar" | "en";
}
```

#### ImportPanel

```typescript
interface ImportPanelProps {
  /** عند اكتمال الاستيراد */
  onImportComplete: (result: ImportFT2BundleResponse) => void;
  /** عند حدوث خطأ */
  onError: (error: Error) => void;
  /** معرّف اللغة */
  lang: "ar" | "en";
}

interface ImportFT2BundleResponse {
  success: boolean;
  device_identity: DeviceIdentity | null;
  txt_imported: boolean;
  pdf_imported: boolean;
  ledger_entry_id: string | null;
  error_message: string | null;
}
```

#### CenterSummary

```typescript
interface CenterSummaryProps {
  summary: CenterReportDTO;
  /** إظهار الرسم البياني */
  showChart?: boolean;
  /** عند النقر على فئة */
  onFilterByStatus: (status: "safe" | "partial" | "rejected") => void;
  /** معرّف اللغة */
  lang: "ar" | "en";
}
```

---

## 5. Custom Hooks Design

### 5.1 `useDeviceData`

```typescript
interface UseDeviceDataReturn {
  devices: DeviceReportDTO[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

function useDeviceData(
  centerId?: string,
  dateRange?: { from: string; to: string }
): UseDeviceDataReturn;
```

**يستخدم:**
- `GET /api/centers/{centerId}/devices` → `CenterReportDTO`
- `GET /api/devices/{deviceId}/history?from=&to=` → `DeviceRepositoryPort.get_device_history()`

### 5.2 `useLanguage`

```typescript
interface UseLanguageReturn {
  lang: "ar" | "en";
  t: (key: string, params?: Record<string, string>) => string;
  isRTL: boolean;
  direction: "rtl" | "ltr";
  switchLang: (lang: "ar" | "en") => void;
}

function useLanguage(): UseLanguageReturn;
```

**يستخدم:** ملفات `ar.json` و `en.json` الموجودة في `src/shared/locales/` — **بدون تغيير**، مجرد تحميل في المتصفح.

### 5.3 `useSafetyEval`

```typescript
interface UseSafetyEvalReturn {
  evaluate: (request: EvaluateColdChainSafetyRequest) => Promise<EvaluateColdChainSafetyResponse>;
  evaluating: boolean;
  lastResult: EvaluateColdChainSafetyResponse | null;
}

function useSafetyEval(): UseSafetyEvalReturn;
```

**يستخدم:** `POST /api/evaluate` → `EvaluateColdChainSafetyUseCase.execute()`

### 5.4 `useImportFT2`

```typescript
interface UseImportFT2Return {
  importFiles: (txtFile: File, pdfFile?: File) => Promise<ImportFT2BundleResponse>;
  importing: boolean;
  lastResult: ImportFT2BundleResponse | null;
}

function useImportFT2(): UseImportFT2Return;
```

**يستخدم:** `POST /api/import` → `ImportFT2BundleUseCase.execute()`

### 5.5 `useLedger`

```typescript
interface UseLedgerReturn {
  entries: LedgerEntry[];
  integrityCheck: () => Promise<{ isValid: boolean; error: string | null }>;
}

function useLedger(deviceId?: string): UseLedgerReturn;
```

**يستخدم:** `LedgerWriterPort.get_chain_state()` + `verify_integrity()`

---

## 6. معالجة الحالات الطرفية

### 6.1 حالات التحميل

```
┌─────────────────────────┐
│  ┌───┐  Loading...      │  ← Skeleton UI
│  │ ◉ │  جاري التحميل    │
│  └───┘                  │
│  ┌──────────┐           │
│  │ ░░░░░░░░ │           │
│  └──────────┘           │
│  ┌──────────────┐       │
│  │ ░░░░░░░░░░░░ │       │
│  └──────────────┘       │
└─────────────────────────┘
```

**المكوّن:** `LoadingSkeleton` مع `aria-busy="true"` و `role="status"`.

### 6.2 الحالة الفارغة

```
┌─────────────────────────────┐
│        📂                   │
│                             │
│  لا توجد أجهزة مسجلة        │
│  No devices registered      │
│                             │
│  [ استيراد ملفات FT2 ]      │
└─────────────────────────────┘
```

**المكوّن:** `EmptyState` مع `role="status"` وزر إجراء.

### 6.3 حالة الخطأ

```
┌─────────────────────────────┐
│  ⚠️ خطأ في الاتصال           │
│  Connection Error            │
│                             │
│  تعذّر الاتصال بالخادم       │
│  retry بعد 30 ثانية          │
│                             │
│  [ إعادة المحاولة ]          │
└─────────────────────────────┘
```

**المكوّن:** `ErrorBoundary` مع `role="alert"` و `aria-live="assertive"`.

### 6.4 حالات خاصة بالنظام

| الحالة | السبب | العرض |
|--------|-------|-------|
| `NO_DATA` | الجهاز بدون قراءات | شارة رمادية + "لا توجد بيانات كافية" |
| `FREEZE_EXCURSION` | Circuit breaker triggered | شارة حمراء + "تجميد — رفض تلقائي" |
| `CRITICAL_HEAT_34C` | >34°C لمدة ساعتين | شارة حمراء + "حرارة حرجة — رفض تلقائي" |
| `CCM index = D` | تراكم حراري مفرط | شارة حمراء + VVM Stage D |
| `HER > 1.5` | تجاوز كامل | شارة حمراء + "استنفاد كامل" |
| `HER 1.0–1.5` | تجاوز جزئي | شارة صفراء + "استنفاد جزئي" |
| License expired | `ILicenseGuard.ensure_active()` فشل | شاشة كاملة مع `role="alertdialog"` |
| SSOT validation failed | مراكز غير مسجلة | تحذير أصفر مع قائمة `unregistered_centers` |

---

## 7. التصميم المتجاوب (Responsive Breakpoints)

```
Mobile (≤640px):
  ┌─────────────┐
  │  Dashboard  │
  ├─────────────┤
  │ DeviceCard  │  ← عمود واحد
  ├─────────────┤
  │ DeviceCard  │
  ├─────────────┤
  │ DeviceCard  │
  └─────────────┘

Tablet (641px–1024px):
  ┌─────────────────────┐
  │    Dashboard         │
  ├──────────┬──────────┤
  │ Device   │ Device   │  ← عمودين
  │  Card    │  Card    │
  ├──────────┴──────────┤
  │  CenterSummary      │
  └─────────────────────┘

Desktop (≥1025px):
  ┌──────────────────────────────────┐
  │  Dashboard  │  Sidebar (Filters) │
  ├────────────┴────────────────────┤
  │ Device │ Device │ Device │ Chart│  ← 3-4 أعمدة + رسم
  └─────────────────────────────────┘

Large Desktop (≥1440px):
  ┌───────────────────────────────────────────┐
  │  Dashboard  │  Sidebar  │  AuditLog Panel  │
  ├─────────────┴───────────┴─────────────────┤
  │ Device │ Device │ Device │ Device │ Chart │  ← 4-5 أعمدة
  └───────────────────────────────────────────┘
```

---

## 8. إمكانية الوصول (Accessibility)

### 8.1 ARIA

| المكوّن | ARIA Attributes |
|---------|----------------|
| `Dashboard` | `role="main"`, `aria-label="لوحة مراقبة سلسلة التبريد"` |
| `DeviceCard` | `role="article"`, `aria-labelledby={deviceId}`, `aria-expanded`, `tabindex="0"` |
| `VVMIndicator` | `role="img"`, `aria-label="مرحلة VVM: {stage}"`, `aria-describedby` |
| `DecisionBadge` | `role="status"`, `aria-live="polite"` |
| `TemperatureChart` | `role="img"`, `aria-label="رسم بياني حراري لجهاز {deviceId}"`, `aria-describedby={tableId}` |
| `LoadingSkeleton` | `aria-busy="true"`, `role="status"` |
| `ErrorBoundary` | `role="alert"`, `aria-live="assertive"` |
| `EmptyState` | `role="status"` |
| `ImportPanel` | `role="region"`, `aria-label="استيراد ملفات FT2"` |

### 8.2 لوحة المفاتيح

| الإجراء | الاختصار |
|---------|----------|
| التنقل بين البطاقات | `Tab` / `Shift+Tab` |
| توسيع/طي بطاقة | `Enter` / `Space` |
| تحديث البيانات | `Ctrl+R` |
| تبديل اللغة | `Ctrl+L` |
| فتح الاستيراد | `Ctrl+I` |
| إغلاق/رجوع | `Escape` |

### 8.3 قارئات الشاشة

- **جميع النصوص** تمر عبر `useLanguage()` → ملفات locales الموجودة → ترجمة كاملة عربي/إنجليزي
- **الألوان وحدها لا تكفي**: كل مؤشر لوني مصحوب بـ:
  - نص وصفي (label)
  - أيقونة emoji (🟢🟡🔴⚪)
  - `aria-label` وصفي
- **الجداول البديلة**: `TemperatureChart` مصحوب بـ `<table>` مخفي (`aria-hidden="false"`) لقارئات الشاشة

### 8.4 التباين العالي

| العنصر | عادي | عالي التباين |
|--------|------|-------------|
| خلفية | `#ffffff` | `#000000` |
| نص أساسي | `#1a1a2e` | `#ffffff` |
| أخضر (SAFE) | `#4CAF50` | `#00FF00` |
| أصفر (PARTIAL) | `#FFC107` | `#FFFF00` |
| أحمر (DISCARD) | `#F44336` | `#FF0000` |
| حدود | `#e0e0e0` | `#ffffff` (2px solid) |

### 8.5 حجم اللمس الأدنى

- جميع الأزرار والبطاقات: **min 44×44px** (WCAG 2.1 AA)
- المسافة بين العناصر: **min 8px**

---

## 9. خريطة API (Backend Routes المقترحة)

كل مسار يوجّه إلى Use Case موجود **بدون تعديل على منطق الأعمال**.

```
GET    /api/health                          → AppComposer.health_check()
GET    /api/devices                         → DeviceRepositoryPort.get_all_device_ids()
GET    /api/devices/{id}/history            → DeviceRepositoryPort.get_device_history()
GET    /api/devices/{id}/report             → GenerateDeviceReportUseCase.execute()
POST   /api/devices/{id}/report/pdf         → GeneratePDFReportUseCase.execute_device_report()
GET    /api/centers                         → IDataRepository.load_centers()
GET    /api/centers/{id}/report             → CenterReportDTO (aggregated)
POST   /api/centers/{id}/report/pdf         → GeneratePDFReportUseCase.execute_center_report()
POST   /api/evaluate                        → EvaluateColdChainSafetyUseCase.execute()
POST   /api/import                          → ImportFT2BundleUseCase.execute()
POST   /api/classify                        → ManageFileLifecycleUseCase.classify_files()
GET    /api/ledger                          → LedgerWriterPort.get_chain_state()
POST   /api/ledger/verify                   → LedgerWriterPort.verify_integrity()
GET    /api/centers/validate                → ValidateCenterMappingUseCase.execute()
POST   /api/verify/{file}                   → VerifyAndRecordUseCase.execute()
GET    /api/specs/{vaccine_type}            → VaccineSpecificationPort.get_spec()
```

---

## 10. حالات الاستخدام (Usage Examples)

### 10.1 Dashboard رئيسي

```tsx
import { Dashboard } from "@/components/Dashboard";
import { useDeviceData, useLanguage } from "@/hooks";

function App() {
  const { lang } = useLanguage();
  const { devices, loading, error, refetch } = useDeviceData();

  return (
    <Dashboard
      devices={devices}
      loading={loading}
      error={error}
      lang={lang}
      onDeviceSelect={(id) => navigate(`/devices/${id}`)}
      onImport={() => navigate("/import")}
      onGenerateReport={(id) => generatePDF(id)}
      onRefresh={refetch}
    />
  );
}
```

### 10.2 بطاقة جهاز مفصّلة

```tsx
<DeviceCard
  report={deviceReport}
  expanded={true}
  onToggle={() => setExpanded(!expanded)}
  onGeneratePDF={handleGeneratePDF}
>
  {/* محتوى موسّع */}
  <VVMIndicator
    stage={deviceReport.vvm_stage}
    size="lg"
    showLabel
    lang="ar"
  />
  <DecisionBadge
    decision={deviceReport.decision}
    variant="full"
    showDescription
    lang="ar"
  />
  <TemperatureChart
    readings={deviceReport.readings}
    thresholds={{ min: 2, max: 8 }}
    showCriticalLines
    lang="ar"
  />
  {deviceReport.decision_reasons.length > 0 && (
    <ul aria-label="أسباب القرار">
      {deviceReport.decision_reasons.map((r) => (
        <li key={r}>{t(r)}</li>
      ))}
    </ul>
  )}
</DeviceCard>
```

### 10.3 لوحة استيراد

```tsx
<ImportPanel
  lang="ar"
  onImportComplete={(result) => {
    if (result.success) {
      showSuccess(t("msg.files_added"));
      refetch();
    } else {
      showError(result.error_message);
    }
  }}
  onError={(e) => showError(e.message)}
/>
```

### 10.4 ملخص مركز

```tsx
<CenterSummary
  summary={centerReport}
  showChart
  lang="ar"
  onFilterByStatus={(status) => setFilter(status)}
/>
{/* يعرض:
    - إجمالي الأجهزة: {total_devices}
    - 🟢 مقبولة: {safe_devices}
    - 🟡 تحت المراقبة: {partial_devices}
    - 🔴 مرفوضة: {rejected_devices}
    - التوصيات: {recommendations[]}
*/}
```

---

## 11. التوافق مع النظام الحالي

### 11.1 ما يُعاد استخدامه كما هو (بدون تعديل)

| الطبقة | الملفات |
|--------|---------|
| **Domain** | كل `src/domain/` — Entities, Value Objects, Enums, Calculators, Engines |
| **Application Use Cases** | كل `src/application/use_cases/` |
| **Application Ports** | كل `src/application/ports/` (29 port) |
| **Infrastructure Adapters** | BerlingerFT2Reader, JsonDeviceRepository, PDF generators |
| **Locales** | `src/shared/locales/ar.json` و `en.json` |
| **Config** | `src/shared/config.py` |
| **DI Container** | `src/shared/di_container.py` |

### 11.2 ما يُضاف فقط

| المكوّن | الوصف |
|---------|-------|
| **FastAPI Backend Layer** | طبقة HTTP رقيقة (~300 سطر) تربط Routes بالـ Use Cases |
| **React Frontend** | المكوّنات المذكورة أعلاه |
| **API DTO Serialization** | تحويل dataclasses → JSON (موجود جزئيًا عبر `to_dict()`) |

### 11.3 ما يُستغنى عنه تدريجيًا

| المكوّن الحالي | البديل |
|----------------|--------|
| `GuardianGUI` (Tkinter) | React Dashboard + DeviceCard |
| `cli.py` (Typer) | يبقى للـ CI/CD والـ scripting |
| PDF Report generators | يُعاد استخدامها كـ Backend endpoints |

---

## 12. ملخص قرارات التصميم

| القرار | السبب |
|--------|-------|
| React + TypeScript | نظام أنواع قوي يطابق DTOs الموجودة، ecosystem واسع لـ accessibility |
| FastAPI كـ Backend | متوافق مع Clean Architecture، auto-generated OpenAPI docs |
| ملفات locales الحالية | لا تكرار — نفس 184 مفتاح عربي/إنجليزي |
| VVMStage.get_color() → CSS variables | ربط مباشر بالألوان المحددة في النظام |
| Decision waterfall موجود → badges ملونة | نفس المنطق: circuit breaker → CCM → HER |
| TemperatureChart + data table مخفي | WCAG 2.1 AA — الرسوم البيانية تحتاج بدائل نصية |
| Skeleton UI + ErrorBoundary + EmptyState | تغطية جميع الحالات الطرفية المطلوبة |
| 44×44px minimum touch targets | WCAG 2.1 AA for touch |
| Keyboard shortcuts + ARIA live regions | دعم كامل لقارئات الشاشة والتنقل بلوحة المفاتيح |

---

## 13. خريطة التنفيذ المقترحة

| المرحلة | المكوّنات | المدة التقديرية |
|---------|-----------|----------------|
| **Phase 1** | FastAPI Backend + API Routes | أسبوع |
| **Phase 2** | Dashboard + DeviceCard + VVMIndicator + DecisionBadge | أسبوعين |
| **Phase 3** | TemperatureChart + CenterSummary + ImportPanel | أسبوعين |
| **Phase 4** | AuditLogViewer + ReportViewer + Accessibility audit | أسبوع |
| **Phase 5** | High-contrast theme + PWA + Offline support | أسبوع |

---

*هذا المقترح مبني بالكامل على الكود الموجود في نظام cci-ft2-intelligence-clean. جميع أسماء الحقول والأنواع والمكوّنات مشتقة مباشرة من Entities و DTOs و Ports الموجودة.*
