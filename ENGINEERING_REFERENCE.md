# CCI-FT2 Intelligence — Technical Reference for New Engineers

> **Document Purpose:** This is a code-derived technical reference for engineers joining the CCI-FT2 Intelligence project. All information is extracted directly from source code — no documentation files, assumptions, or speculation were used.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Pattern](#2-architecture-pattern)
3. [Directory Structure](#3-directory-structure)
4. [Entry Points](#4-entry-points)
5. [Core Domain Model](#5-core-domain-model)
6. [Scientific Calculators](#6-scientific-calculators)
7. [Decision Engines](#7-decision-engines)
8. [Application Layer — Use Cases](#8-application-layer--use-cases)
9. [Data Transfer Objects](#9-data-transfer-objects)
10. [Infrastructure Adapters](#10-infrastructure-adapters)
11. [Presentation Layer](#11-presentation-layer)
12. [Security & Licensing](#12-security--licensing)
13. [Internationalization (i18n)](#13-internationalization-i18n)
14. [Testing Strategy](#14-testing-strategy)
15. [Configuration Management](#15-configuration-management)
16. [Dependency Management](#16-dependency-management)
17. [CI/CD Pipeline](#17-cicd-pipeline)
18. [Key Design Patterns](#18-key-design-patterns)
19. [Known Technical Debt](#19-known-technical-debt)
20. [How to Extend the System](#20-how-to-extend-the-system)

---

## 1. System Overview

**What it is:** A Cold Chain Intelligence (CCI) system for monitoring vaccine cold chain safety. It processes temperature data from Berlinger Fridge-Tag 2 (FT2) devices, evaluates thermal exposure using WHO scientific standards, and produces safety decisions with professional bilingual (Arabic/English) PDF reports.

**What it does NOT have:**
- No HTTP API or web server (no FastAPI, Flask, Django)
- No active PostgreSQL usage (the docker-compose defines one, but no Python code connects to it)
- No background task scheduler (no Celery, APScheduler)
- No real-time streaming or WebSocket

**Tech stack (from `requirements.txt`):**
| Category | Libraries |
|---|---|
| PDF Generation | `reportlab==4.4.9`, `pillow==12.1.0` |
| Arabic RTL | `arabic-reshaper==3.0.0`, `python-bidi==0.6.7` |
| Visualization | `matplotlib==3.10.8` |
| CLI | `typer==0.12.3`, `click==8.1.7` |
| PDF Analysis | `pdfminer.six==20260107`, `pypdf==6.7.4` |
| Security | `cryptography==46.0.5`, `cffi==2.0.0` |
| Data | `PyYAML==6.0.3`, `python-dateutil==2.9.0.post0` |
| File Locking | `filelock>=3.12.0` |

**Storage strategy:** File-based (JSON, YAML, JSONL, Parquet). No relational database is actively used in the codebase despite PostgreSQL being defined in docker-compose.yml.

---

## 2. Architecture Pattern

The system follows **Clean Architecture / Hexagonal Architecture** with strict layer separation enforced by architecture tests.

```
┌─────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                   │
│  CLI (Typer) │ GUI (Tkinter) │ PDF Reporters        │
├─────────────────────────────────────────────────────┤
│                 APPLICATION LAYER                    │
│  Use Cases │ DTOs │ Ports (Interfaces) │ Mappers    │
├─────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE LAYER                 │
│  Adapters │ Repositories │ Security │ PDF │ Ledger  │
├─────────────────────────────────────────────────────┤
│                   DOMAIN LAYER                       │
│  Entities │ Value Objects │ Services │ Calculators   │
│  Engines  │ Rules        │ Policies │ Enums          │
└─────────────────────────────────────────────────────┘
```

**Dependency Rule:** Inner layers know nothing about outer layers. Domain has zero external dependencies. This is enforced by:
- `tests/architecture/` — layer separation tests
- `scripts/check_domain_purity.py` — ensures domain imports nothing from outer layers
- `scripts/check_layer_dependencies.py` — validates layer dependency direction
- `scripts/project_tree_guard.py` — enforces project structure

---

## 3. Directory Structure

```
cci-ft2-intelligence-clean/
├── src/
│   ├── domain/                    # CORE — pure business logic
│   │   ├── entities/              # FT2Entry, Vaccine, ThermalRecord, DeviceIdentity, etc.
│   │   ├── value_objects/         # AnalysisResult, VaccineSpecification, HERResult, CCMResult
│   │   ├── services/              # ExposureAnalysisService, RegulatoryDecisionService, RulesEngine, JudgmentEngine
│   │   ├── calculators/           # CCMCalculator, HERCalculator, Q10ThermalCalculator, MKTCalculator
│   │   ├── engines/               # ReferenceExposureEngine, HeatExposureEngine
│   │   ├── rules/                 # HeatExposureRule, VVMStageRule
│   │   ├── policies/              # TrialPolicy (trial period enforcement)
│   │   ├── enums/                 # VVMStage, VaccineStatus, FileStatus, LedgerEvent, EvidenceGrade
│   │   ├── ledger/                # LedgerEntry, LedgerChainState (immutable audit chain)
│   │   ├── evidence/              # EvidenceIntegrityReport, VerificationResult
│   │   ├── models/                # TemperatureExposure
│   │   ├── validators/            # FT2EntryValidator
│   │   └── exceptions/            # Domain-specific exceptions
│   │
│   ├── application/               # USE CASES & application services
│   │   ├── use_cases/             # 20 use cases (GenerateDeviceReport, ImportFT2Bundle, etc.)
│   │   ├── dtos/                  # 14 DTOs (AnalysisResultDTO, DeviceReportDTO, etc.)
│   │   ├── ports/                 # ~30 interface definitions (repository ports, generator ports)
│   │   ├── services/              # Application services (AnalysisResultService, FileLock, etc.)
│   │   ├── mappers/               # CenterMapper, ExposureMapper, VaccineMapper
│   │   ├── security/              # LicenseValidator
│   │   └── app_composer.py        # Composition root — DI container
│   │
│   ├── infrastructure/            # ADAPTERS — I/O, storage, security
│   │   ├── adapters/              # FT2 readers, JSON repositories, PDF generators
│   │   │   ├── ft2_reader/        # FT2 parsing sub-package (models, parser, services, validator)
│   │   │   ├── reporting/         # PDF reporting (new_pdf_engine, components, strategy)
│   │   │   └── metrics/           # Performance monitoring
│   │   ├── repositories/          # DeviceDataRepository, YAMLVaccineSpecRepository
│   │   ├── security/              # LicenseGuard, EncryptedLicenseRepository, FingerprintProvider
│   │   ├── storage/               # Parquet and file storage adapters
│   │   ├── pdf/                   # PDF extraction and generation
│   │   ├── ingestion/             # Data ingestion pipeline
│   │   ├── ledger/                # Immutable audit ledger (JSONL)
│   │   ├── lifecycle/             # File lifecycle management
│   │   ├── registry/              # Device/center registry
│   │   ├── validation/            # Data validation
│   │   └── utils/                 # VaccineLibraryLoader
│   │
│   ├── presentation/              # UI & reporting
│   │   ├── cli/                   # cli.py (Typer CLI), gui_main.py (Tkinter GUI)
│   │   ├── reporting/             # PDF generators (ArabicPDFGenerator, ProfessionalPDFGenerator, etc.)
│   │   │   ├── components/        # ArabicProcessor, ChartBuilder, HeaderBuilder, TableBuilder
│   │   │   └── professional/      # ChartGenerator, ProfessionalVaccineReport
│   │   └── messages/              # MessageMap (i18n message map)
│   │
│   ├── shared/                    # Cross-cutting utilities
│   │   ├── locales/               # Translation files (ar, en)
│   │   ├── utils/                 # PathUtils
│   │   ├── fonts/                 # Shared fonts for PDF
│   │   ├── language_manager.py    # Singleton i18n manager (Arabic/English)
│   │   ├── config.py              # Environment config (CCI_ENV, CCI_DATA_ROOT, CCI_LOG_LEVEL)
│   │   └── di_container.py        # Lightweight DI container
│   │
│   └── utils/                     # General utilities
│
├── tests/                         # Multi-level test suite
│   ├── unit/                      # Domain entities, calculators, rules, DTOs, services
│   ├── integration/               # Full use case flows, ledger, license, PDF, VVM scenarios
│   ├── bdd/                       # Scenario-based tests (excursion device, safe device)
│   ├── golden/                    # PDF golden master, reference cold chain golden
│   ├── architecture/              # Layer separation, domain purity, dependency isolation
│   ├── contracts/                 # Architecture contracts, domain invariants, public contracts
│   ├── regression/                # Scientific regression tests
│   ├── performance/               # PDF generation speed benchmark
│   ├── reporting/                 # Center report snapshot tests
│   ├── fixtures/ft2/              # FT2 sample data (PDF and TXT)
│   └── helpers/                   # TimeFactory (time manipulation)
│
├── scripts/                       # Operational scripts
│   ├── run_ft2_pipeline.py        # Main pipeline runner
│   ├── generate_pdf_report.py     # Standalone PDF generation
│   ├── health_check.py            # Health check
│   ├── license_guard.py           # License management
│   ├── audit_ledger.py            # Ledger verification
│   ├── check_domain_purity.py     # Architecture guard — domain layer
│   ├── check_layer_dependencies.py# Architecture guard — layer dependencies
│   └── project_tree_guard.py      # Project structure enforcement
│
├── config/                        # Configuration files
│   ├── base.yaml                  # App name, version, data_root, log_level
│   ├── production.yaml            # Production settings
│   ├── development.yaml           # Development settings
│   ├── testing.yaml               # Testing settings
│   ├── thresholds.yaml            # Safety thresholds
│   ├── center_profiles.yaml       # Center profiles
│   └── vaccine_library.yaml       # Vaccine definitions
│
├── data/                          # Data directories
│   ├── input_ft2/                 # Input FT2 data files
│   ├── output/                    # Generated reports, cycles
│   ├── parquet/                   # Parquet session storage
│   ├── ledger/                    # Audit ledger
│   ├── registry/                  # Device registry
│   └── archive/                   # Archived data
│
├── assets/                        # Static assets (fonts, PNG images)
├── config.yaml                    # LLM model configuration (Groq/Ollama)
├── docker-compose.yml             # Docker services (app + PostgreSQL)
├── Dockerfile                     # Container definition (python:3.12-slim)
├── conftest.py                    # pytest root configuration
├── .pre-commit-config.yaml        # Pre-commit hooks (black, isort, bandit, etc.)
├── .pylintrc                      # Pylint configuration
└── requirements.txt               # Production dependencies
```

---

## 4. Entry Points

### 4.1 CLI Entry Point

**File:** `src/presentation/cli/cli.py`

**Registered script name:** `ft2-cli` (defined in `pyproject.toml` as `ft2-cli = "src.presentation.cli.cli:main"`)

**Commands:**

| Command | Description | Parameters |
|---|---|---|
| `health_check` | System readiness check | None |
| `import_data` | Import FT2 data from directory | `--input/-i` (required), `--output/-o` (default: `ft2_data.json`) |
| `generate_device_report` | Generate single device report | `device_id` (arg), `--output/-o`, `--data/-d` |
| `generate_all_device_reports` | Generate all device reports | `--output/-o`, `--data/-d` (stub — "coming in next release") |

**Usage example:**
```bash
ft2-cli health-check
ft2-cli import-data --input ./input_ft2/ --output ft2_data.json
ft2-cli generate-device-report FT12345 --output report.json --data ft2_data.json
```

### 4.2 GUI Entry Point

**File:** `src/presentation/cli/gui_main.py`

**Run with:**
```bash
python src/presentation/cli/gui_main.py
```

**Features:**
- Tkinter-based desktop GUI
- Arabic/English language toggle (menu bar)
- FT2 file selection (TXT/PDF) from any path
- Per-device or full-cycle PDF report generation with date range filtering
- Cycle save/load (JSON persistence to `data/output/cycles/`)
- Health check on startup via `AppComposer.health_check()`
- Cycle ID auto-generation: `CC-{timestamp}`

### 4.3 Composition Root

**File:** `src/application/app_composer.py`

`AppComposer` is the **Dependency Injection container**. It wires all use cases with their dependencies:

| Factory Method | Returns |
|---|---|
| `create_generate_device_report_uc()` | `GenerateDeviceReportUseCase` |
| `create_generate_pdf_report_uc()` | `GeneratePDFReportUseCase` |
| `create_import_ft2_bundle_uc()` | `ImportFT2BundleUseCase` |
| `health_check()` | `bool` — instantiates all use cases to verify wiring |

**License Guard initialization:**
- Reads public key from `~/.cci_ft2/public.pem`
- Reads license from `~/.cci_ft2/license.dat`
- In `development`/`test` environments, creates dummy files if missing
- Uses `SystemFingerprintProvider` for machine binding
- Trial period: 365 days

---

## 5. Core Domain Model

### 5.1 Key Entities

| Entity | File | Mutability | Description |
|---|---|---|---|
| `FT2Entry` | `domain/entities/ft2_entry.py` | Mutable | Single day FT2 reading: min/max/avg temps, alarms, freeze/CCM minutes |
| `TemperatureReading` | `domain/entities/temperature_reading.py` | Mutable | Individual temperature measurement for a vaccine at a specific time |
| `ThermalRecord` | `domain/entities/thermal_record.py` | Frozen | Immutable device-specific thermal measurement event |
| `Vaccine` | `domain/entities/vaccine.py` | Mutable | Vaccine with thermal tolerance thresholds, Q10 VVM model parameters |
| `VaccineBatch` | `domain/entities/vaccine_batch.py` | Frozen | Tracked batch with exposure history; `accumulate_exposure()` → status |
| `DeviceIdentity` | `domain/entities/device_identity.py` | Frozen | Unified device identity (device_id + serial_number + optional center_id) |
| `DeviceReport` | `domain/entities/device_report.py` | Frozen | Domain object for device reports |
| `CoolingDevice` | `domain/entities/cooling_device.py` | Frozen | Physical cooling device with `evaluate_safety()` method |
| `VaccinationCenter` | `domain/entities/vaccination_center.py` | Mutable | Aggregating entity with freeze detection, CCM tracking, device list |
| `EquipmentRecord` | `domain/entities/equipment_record.py` | Frozen | Middle layer between device and center |
| `EquipmentVaccine` | `domain/entities/equipment_vaccine.py` | Frozen | Vaccine batch inside specific cooling equipment with VVM stage |
| `DeviceLink` | `domain/entities/device_link.py` | Frozen | Device replacement record with cold chain continuity tracking |
| `HeatExposure` | `domain/entities/heat_exposure.py` | Frozen | Heat exposure during single cold chain stage |
| `ArchiveRecord` | `domain/entities/archive_record.py` | Frozen | Archive lifecycle with forensic integrity (SHA-256, immutable transitions) |
| `RetentionPolicy` | `domain/entities/retention_policy.py` | Frozen | File retention policy (90 days default, 365 for "CRITICAL" devices) |

### 5.2 Key Value Objects

| Value Object | File | Description |
|---|---|---|
| `AnalysisResult` | `domain/value_objects/analysis_result.py` | Unified thermal analysis: HER ratio, CCM index, circuit breaker status |
| `VaccineSpecification` | `domain/value_objects/vaccine_specification.py` | Scientific spec: Q10 factor, shelf life, critical temp, VVM type. Includes `VACCINE_CATALOGUE` (12 vaccines) |
| `HERResult` | `domain/value_objects/her_result.py` | Pure HER calculation result |
| `CCMResult` | `domain/value_objects/ccm_result.py` | Pure CCM calculation result (Delta + AUC) |
| `ReferenceEngineResult` | `domain/value_objects/reference_engine_result.py` | Reference audit result (Arrhenius + MKT) |
| `TemperatureEntry` | `domain/value_objects/temperature_entry.py` | Immutable temperature entry with device_id |
| `FileIngestionRecord` | `domain/value_objects/file_ingestion_record.py` | File identity in lifecycle (SHA-256 hash, device_id, status) |

### 5.3 Key Enums

| Enum | Values |
|---|---|
| `VaccineStatus` | `SAFE`, `PARTIAL`, `DISCARD` |
| `VVMStage` | `NONE=1`, `A=2`, `B=3`, `C=4`, `D=5` |
| `SafetyStatus` | `SAFE`, `PARTIAL`, `DISCARD`, `NO_DATA` |
| `VaccineDecision` | `SAFE`, `PARTIAL`, `DISCARD`, `EXPIRED` |
| `DecisionReason` | `WITHIN_LIMITS`, `PARTIAL_EXPOSURE`, `HEAT_EXCESS`, `CCM_BREAK`, `FREEZE_EVENT`, `VVM_CRITICAL`, `EXPIRED` |
| `FileStatus` | `PENDING`, `VALIDATED`, `PROCESSING`, `PROCESSED`, `ARCHIVED`, `QUARANTINED` (state machine with valid transitions) |
| `LedgerEvent` | 70+ events across categories: FT2, REPORT, VACCINE, UNIT, CYCLE, OPERATOR, ERROR, SYSTEM, AUDIT, LICENSE |
| `EvidenceGrade` | `A_PLUS(100)`, `A(90)`, `B(75)`, `C(60)`, `F(0)` |
| `EquipmentType` | `REFRIGERATOR`, `COLD_ROOM`, `FREEZER`, `DEEP_FREEZER`, `TRANSPORT_BOX` |
| `DeviceStatus` | `ACTIVE`, `RETIRED`, `REPLACED` |
| `RiskLevel` | `SAFE`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `ArchiveStatus` | `PROCESSING`, `ARCHIVED`, `QUARANTINED`, `EXPIRED`, `DELETING`, `DELETED`, `MISSING` |
| `TrialStatus` | `ACTIVE`, `EXPIRED`, `TAMPERED` |

### 5.4 Vaccine Catalogue (from `VaccineSpecification`)

The system has a built-in catalogue of 12 vaccine types:

| Vaccine | Q10 | Shelf Life (days) | VVM Type | Freeze-Sensitive |
|---|---|---|---|---|
| OPV | 3.6 | 126 | VVM2 | No |
| HEPB | 2.0 | 1460 | VVM30 | Yes |
| DTP | 2.0 | 548 | VVM14 | Yes |
| DT | 2.0 | 548 | VVM14 | Yes |
| TT | 2.0 | 548 | VVM14 | No |
| TD | 2.0 | 548 | VVM14 | No |
| BCG | 2.0 | 365 | VVM14 | No |
| MEASLES | 2.0 | 365 | VVM2 | No |
| MMR | 2.0 | 365 | VVM2 | No |
| YF | 2.0 | 730 | VVM2 | No |
| IPV | 2.0 | 730 | VVM14 | Yes |
| GENERAL | 2.0 | 730 | VVM14 | No |

---

## 6. Scientific Calculators

All calculators are in `src/domain/calculators/`.

### 6.1 CCM Calculator (Cold Chain Minutes)

**File:** `ccm_calculator.py`

**Methods:**
- `calculate_delta()` — absolute temperature differences from base temp
- `calculate_auc()` — area under curve above base temp
- `calculate()` — returns both delta and AUC

**Time unit:** Minutes (enforced by `TIME_UNIT` constant)

### 6.2 Time-Weighted CCM Calculator

**File:** `time_weighted_ccm_calculator.py`

**Methods:**
- `calculate()` — Enhanced CCM with time-weighted delta and trapezoidal AUC integration

### 6.3 HER Calculator (Heat Exposure Ratio)

**File:** `her_calculator.py`

**Methods:**
- `calculate(exposure_minutes, full_duration)` — Simple ratio

### 6.4 Q10 HER Calculator

**File:** `q10_her_calculator.py`

**Methods:**
- `calculate_her(readings)` — Q10 model with sampling gap protection
- Scientific constants: Q10=2.0, Tref=5.0°C, shelf_life=48h, max_gap=2h

### 6.5 Arrhenius HER Calculator

**File:** `arrhenius_her_calculator.py`

**Methods:**
- `calculate(entries, shelf_life_hours)` — Arrhenius-based HER for parallel reference audit
- Ea=83.144 kJ/mol

### 6.6 Q10 Thermal Calculator

**File:** `q10_thermal_calculator.py`

**Methods:**
- `evaluate(temperature, duration_minutes, reference_temp/spec)` — Returns SAFE/PARTIAL/DISCARD
- `calculate_q10_impact(entries, reference_temp)` — Weighted average Q10 factor

### 6.7 MKT Calculator (Mean Kinetic Temperature)

**File:** `mkt_calculator.py`

**Methods:**
- `calculate(entries)` — Mean Kinetic Temperature via Arrhenius equation
- Ea=83.144 kJ/mol, R=8.314 J/mol·K

### 6.8 VVM Q10 Model

**File:** `vvm_q10_model.py`

**Methods:**
- `calculate_acceleration_factor(actual_temp)` — Returns 1.0 for freeze (<0°C) or temp ≤ ideal; uses Q10^((temp-ideal)/10) for heat
- `calculate_cumulative_degradation_hours(readings)` — Cumulative degradation

---

## 7. Decision Engines

### 7.1 ExposureAnalysisService

**File:** `src/domain/services/exposure_analysis_service.py`

**The core thermal analysis engine.** Produces unified `AnalysisResult` with HER ratio, CCM index, circuit breaker detection. Based on WHO/IVB/06.10 + WHO/PQS/E06/IN02.1.

**Key method:** `analyze(readings, spec, supply_date, enable_supply_date)`

**Pipeline:**
1. `_check_circuit_breakers(readings, spec)` — Detects FREEZE_EXCURSION or CRITICAL_HEAT_34C (instant DISCARD)
2. `_calculate_her_ratio(readings, spec)` — Q10 (Arrhenius) model; supports both duration-bearing and pairwise timestamp readings
3. `_calculate_ccm_index(hours_above_10, hours_above_34)` — WHO CCM thresholds:

| CCM Index | Threshold |
|---|---|
| D | >2h at 34°C |
| ABC | >336h at 10°C |
| AB | >192h at 10°C |
| A | >72h at 10°C |
| 0 | <72h at 10°C |

### 7.2 VaccineAssessmentService

**File:** `src/domain/services/vaccine_assessment_service.py`

**Core vaccine safety decision engine.** Implements fail-fast hierarchical decision cascade:

```
1. Expiry check → EXPIRED
2. VVM stage 3/4 → DISCARD
3. Circuit Breaker (freeze or 34°C+) → DISCARD
4. CCM index D → DISCARD
5. HER > 1.5 → DISCARD
6. HER > 1.0 → PARTIAL
7. HER <= 1.0 → SAFE
```

**Key method:** `assess(vaccine, readings, spec, reference_date)`

### 7.3 RegulatoryDecisionService

**File:** `src/domain/services/regulatory_decision_service.py`

Issues decisions based purely on regulatory temperature/duration limits (no probabilistic models).

**Decision rules (by priority):**
1. Freeze-sensitive vaccine at ≤ 0°C → DISCARD
2. Frozen storage vaccine in freeze range → SAFE
3. Temperature above max_heat_temp → DISCARD
4. Temperature above max_temp with duration ≥ max_heat_duration_hours → DISCARD; otherwise PARTIAL
5. Within range → SAFE

**Key method:** `evaluate(temperature, duration_minutes, spec)` → "SAFE" | "PARTIAL" | "DISCARD"

### 7.4 RulesEngine (Domain Layer)

**File:** `src/domain/services/rules_engine.py`

Chain-of-responsibility pattern for rule-based decision making on center/device data.

**Rules in order:**
1. `ExpiryRule` — Checks expiry date
2. `VVMStageRule` — Maps HER ratio to VVM stages (A/B/C/D)
3. `ThawRule` — Checks thaw duration for ultra-cold chain
4. `FreezeRule` — Handles freeze violations vs freeze-resistant vaccines
5. `HeatCriticalRule` — Critical temperature or CCM breach
6. `HeatDurationRule` — Duration-based heat exposure (feature-flagged)
7. `TemperatureWarningRule` — Warning for out-of-range (2-8°C) without rejection
8. `DefaultRule` — Returns "ACCEPTED"

**Key method:** `RulesEngine.run(center, stats)` — Iterates rules; sets `center.decision` on first match

### 7.5 JudgmentEngine (Domain Layer)

**File:** `src/domain/services/judgment_engine.py`

Human-readable explanation layer on top of RulesEngine decisions. Translates technical decisions into Arabic narratives with risk levels, confidence scores, and recommendations.

**Key method:** `judge(decision, decision_reason, her_ratio, ccm_index, freeze_detected, has_critical_heat, vaccine_spec, confidence)` → `JudgmentOutput`

**Confidence calculation:**
- Starts at 1.0
- Deducts: freeze (-0.15), critical heat (-0.2), high HER (-0.1/-0.2), high CCM (-0.1/-0.15)
- Minimum confidence: 0.5

**Human review needed when:** DISCARD, HER≥0.9, freeze, confidence<0.75, CCM D/ABC

### 7.6 ScientificReferenceService

**File:** `src/domain/services/scientific_reference_service.py`

Audit-only parallel scientific reference analysis using Arrhenius + MKT models. Does NOT change legacy decisions.

**Key method:** `analyze(entries, vaccine_type, supply_date)` → dict with reference HER, MKT, Ea, traceability metadata

### 7.7 ThermalDegradationEstimator

**File:** `src/domain/services/thermal_degradation_estimator.py`

Scientific estimates ONLY (advisory). Never influences decision path. Estimates remaining potency and shelf life using simplified Q10 model.

**Key methods:**
- `estimate_remaining_potency(thermal_history, spec)` → remaining potency %
- `calculate_cumulative_impact(thermal_history, spec)` → dict with freeze/heat events, total heat hours, remaining shelf life %

---

## 8. Application Layer — Use Cases

All use cases are in `src/application/use_cases/`. They follow the `BaseUseCase` abstract pattern requiring an `execute()` method.

| Use Case | File | Responsibility |
|---|---|---|
| `GenerateDeviceReportUseCase` | `generate_device_report_uc.py` | Core device report: regulatory decisions, thermal excursions, advisory data, ledger recording |
| `GenerateDeviceReportUCPhase2` | `generate_device_report_uc_phase2.py` | Phase 2 with performance monitoring |
| `GenerateCenterReportUCPhase2` | `generate_center_report_uc_phase2.py` | Center-level report with ledger and performance monitoring |
| `GeneratePDFReportUseCase` | `generate_pdf_report_uc.py` | Orchestrates PDF generation for device and center reports |
| `GenerateVaccinesReportUseCase` | `generate_vaccines_report_uc.py` | Vaccine assessment TSV report with summary counts |
| `GenerateReportUseCase` | `generate_report_uc.py` | Phase 5 placeholder |
| `ImportFT2BundleUseCase` | `import_ft2_bundle_uc.py` | Atomic import of FT2 bundles (TXT + PDF) with device identity and ledger |
| `ImportFt2DataUseCase` | `import_ft2_data_uc.py` | Legacy FT2 data import with optional center-context enrichment |
| `EvaluateColdChainSafetyUseCase` | `evaluate_cold_chain_safety_use_case.py` | **Main orchestration use case**: chains ExposureAnalysis → ScientificReference → RulesEngine → JudgmentEngine |
| `EvaluateScientificReferenceUseCase` | `evaluate_scientific_reference_use_case.py` | Parallel reference audit without changing legacy decision |
| `ReconcileLegacyVsReferenceUseCase` | `reconcile_legacy_vs_reference_use_case.py` | Compares legacy HER with reference HER; flags if delta > 0.05 |
| `TrackBatchExposureUseCase` | `track_batch_exposure_uc.py` | Batch-level exposure tracking |
| `ValidateCenterMappingUseCase` | `validate_center_mapping.py` | SSOT center mapping validation (YAML vs data) |
| `ManageFileLifecycleUseCase` | `manage_file_lifecycle.py` | File classification: ready_for_processing, already_processed, quarantine |
| `RecordVerificationUseCase` | `record_verification_uc.py` | Records verification events in forensic ledger |
| `VerifyAndRecordUseCase` | `verify_and_record_uc.py` | Orchestrates file verification and records in ledger |

### 8.1 Key Use Case: EvaluateColdChainSafetyUseCase

This is the most important use case — it chains the full analysis pipeline:

```
Request → Build DomainCenterContext
        → ExposureAnalysisService.analyze() (HER + CCM + Circuit Breakers)
        → ScientificReferenceService.analyze() (parallel audit, feature-flagged)
        → RulesEngine.apply_rules() (decision rules)
        → JudgmentEngine.judge() (human-readable explanation)
        → Response
```

**Feature flags that control behavior:**
- `CCI_ENABLE_SUPPLY_DATE` — Supply date filtering
- `CCI_ENABLE_HEAT_DURATION` — Heat duration rule
- `CCI_ENABLE_REFERENCE_AUDIT` — Parallel scientific reference audit

---

## 9. Data Transfer Objects

All DTOs are in `src/application/dtos/`. They implement the `BaseDTO` protocol requiring `to_dict() -> Mapping[str, Any]`.

### 9.1 AnalysisResultDTO

**File:** `analysis_result_dto.py`

```python
@dataclass(frozen=True)  # immutable
class AnalysisResultDTO:
    vaccine_id: str
    status: VaccineStatus  # SAFE, PARTIAL, DISCARD
    her: float
    ccm: float
    vvm_stage: VVMStage = VVMStage.NONE
    alert_level: str = "GREEN"
    category_display: str = ""
    thaw_remaining_hours: Optional[float] = None
    is_thawing: bool = False
    stability_budget_consumed_pct: float = 0.0
    decision_reasons: Tuple[str, ...] = ()
    audit_log: Tuple[dict, ...] = ()
    recommendations: Tuple[str, ...] = ()
```

**Key properties:**
- Frozen (immutable) — no `add_reason()` or `generate_recommendations()` methods exist
- `VaccineStatus` enum: SAFE, PARTIAL, DISCARD
- `VVMStage` enum: NONE, A, B, C, D

### 9.2 DeviceReportDTO

**File:** `device_report_dto.py`

The most comprehensive DTO. Contains embedded enums:

```python
class ReportDecision(str, Enum):
    ACCEPTED, REJECTED_HEAT_C, REJECTED_FREEZE, REJECTED_EXPIRED,
    REJECTED_THAW, PARTIAL, SAFE, UNKNOWN

class VVMStage(str, Enum):
    A, B, C, D
```

**Validation (`__post_init__`):**
- `device_id` cannot be empty
- `center_id` cannot be empty
- `stability_budget_consumed_pct` must be between 0 and 100
- `decision` must be a `ReportDecision` instance
- `vvm_stage` must be a `VVMStage` instance
- If both min and max in `temperature_ranges`, min must not exceed max

**Methods:**
- `get_batch_counts()` — counts excursions by impact level
- `create_golden_baseline()` — factory for test baseline

### 9.3 Other DTOs

| DTO | Type | Key Fields |
|---|---|---|
| `CenterDTO` | Mutable | id, name, equipment, temperature_ranges, device_ids, ft2_entries, decision, vvm_stage |
| `CenterReportDTO` | Frozen | center_id, total/safe/rejected/partial devices, devices list, recommendations |
| `CenterStatsDTO` | Frozen | center_id, num_ft2_entries, has_freeze, has_heat, avg/min/max temperature |
| `EquipmentDTO` | Mutable | equipment_id, device_id, center_id, temperature_ranges, ft2_entries, decision |
| `FT2EntryDTO` | Mutable | id, device_id, timestamp, temperature, duration_minutes, freeze/heat risk flags |
| `ThermalExcursionDTO` | Frozen | device_id, excursion_type (HEAT/FREEZE), duration_minutes, impact_level |
| `VaccineDTO` | Mutable | id, category, q10_value, ideal_temp, shelf_life_days, thaw info |
| `ReportInputDTO` | Frozen | center_id, period_start/end, metrics (Tuple), meta (Mapping) — deep immutability |
| `FileClassificationResult` | Mutable | run_id, ready_for_processing, already_processed, quarantine |
| `ValidationResult` | Frozen | is_ssot_valid, yaml_count, affected_count, unregistered_centers |

### 9.4 Request/Response DTOs

| DTO | File | Fields |
|---|---|---|
| `GenerateDeviceReportRequest` | `requests.py` | device_id, operator, cycle_id, date_from, date_to |
| `EvaluateColdChainSafetyRequest` | `evaluate_cold_chain_safety_request.py` | center_id, readings (Tuple[TemperatureReading]), vaccines, vaccine_spec, temperature_ranges |
| `EvaluateColdChainSafetyResponse` | `evaluate_cold_chain_safety_request.py` | center_id, decision, vvm_stage, her_ratio, ccm_index, judgment_risk, confidence |
| `ImportFT2BundleRequest` | `import_ft2_bundle_uc.py` | txt_path, pdf_path, device_id, serial_number |
| `ImportFT2BundleResponse` | `import_ft2_bundle_uc.py` | success, device_identity, txt_imported, pdf_imported, ledger_entry_id |

---

## 10. Infrastructure Adapters

All adapters are in `src/infrastructure/adapters/`.

### 10.1 FT2 Readers

| Adapter | File | Description |
|---|---|---|
| `BerlingerFT2Reader` | `berlinger_ft2_reader.py` | Parses Berlinger FT2 TXT/PDF files |
| `DefaultFT2Reader` | `default_ft2_reader.py` | Default FT2 reading implementation |
| `FT2ReaderAdapter` | `ft2_reader_adapter.py` | Adapter interface for FT2 reading |

**FT2 Reader sub-package** (`ft2_reader/`):
- `models/` — FT2 data models
- `parser/ft2_parser.py` — FT2 file parsing
- `services/ft2_linker.py` — Links FT2 data to equipment
- `validator/ft2_validator.py` — FT2 data validation

### 10.2 Repositories

| Adapter | File | Storage | Description |
|---|---|---|---|
| `DeviceDataRepository` | `repositories/device_repository.py` | JSON | Main device data storage |
| `JSONDeviceRepository` | `adapters/json_device_repository.py` | JSON | JSON-based device repository |
| `JSONVaccineRepository` | `adapters/json_vaccine_repository.py` | JSON | JSON vaccine data |
| `JSONVaccineSpecRepository` | `adapters/json_vaccine_spec_repository.py` | JSON/JSONL | Vaccine specifications |
| `YAMLVaccineSpecRepository` | `repositories/yaml_vaccine_spec_repository.py` | YAML | YAML vaccine specifications |
| `EquipmentVaccineRepository` | `adapters/equipment_vaccine_repository.py` | — | Equipment-vaccine linkage |
| `JSONLIndexAdapter` | `adapters/jsonl_index_adapter.py` | JSONL | JSON Lines indexing |

### 10.3 PDF Generation

| Adapter | File | Description |
|---|---|---|
| `PDFGenerator` | `adapters/reporting/new_pdf_engine.py` | WeasyPrint-based PDF generation (new engine) |
| `PDFReportGenerator` | `adapters/pdf_report_generator.py` | ReportLab-based PDF generation |

**Reporting sub-package** (`adapters/reporting/`):
- `components/` — Alert circle, stability bar, VVM icon components
- `pdf_strategy.py` — PDF generation strategy
- `unified_pdf_generator_wrapper.py` — Wrapper for unified PDF generation

### 10.4 Other Adapters

| Adapter | File | Description |
|---|---|---|
| `FileSystemAdapter` | `filesystem_adapter.py` | File system operations |
| `LedgerWriterAdapter` | `ledger_writer_adapter.py` | Append-only ledger writes |
| `ValidationProtocolService` | `validation_protocol_service.py` | Returns validation protocols for vaccine types |
| `BerlingerVerifierAdapter` | `berlinger_verifier_adapter.py` | Device verification |
| `NoopReporterAdapter` | `noop_reporter_adapter.py` | Null object pattern |

---

## 11. Presentation Layer

### 11.1 CLI (Typer)

**File:** `src/presentation/cli/cli.py`

Uses `typer.Typer()` with 4 commands. Entry point wired through `AppComposer`.

### 11.2 GUI (Tkinter)

**File:** `src/presentation/cli/gui_main.py`

`GuardianGUI` class:
- Window: 1200x800
- Menu bar: File (save/load cycle, exit), Help (about), Language toggle
- Dashboard: 6 action buttons (general data, units, vaccines, FT2 files, verify, generate PDF)
- Results table: Unit, Vaccine, Status, Decision columns
- Status bar at bottom
- Auto-saves cycle on close

### 11.3 PDF Reporters

Located in `src/presentation/reporting/`:

| Reporter | File | Description |
|---|---|---|
| `ArabicPDFGenerator` | — | Arabic-language PDF generation |
| `PDFGenerator` | — | Base PDF generator |
| `ProfessionalPDFGenerator` | — | Professional bilingual PDF |
| `SimplePDFGenerator` | — | Simple PDF output |
| `UnifiedPDFGenerator` | — | Unified PDF generation |
| `CSVReporter` | — | CSV report output |
| `Guard` | — | Guard/policy enforcement in reports |

**Components** (`reporting/components/`):
- `ArabicProcessor` — Arabic text processing
- `ChartBuilder` — Chart generation
- `HeaderBuilder` — Report headers
- `PageLayoutBuilder` — Page layout
- `TableBuilder` — Table generation

**Professional reports** (`reporting/professional/`):
- `ChartGenerator` — Professional charts
- `ProfessionalVaccineReport` — Professional vaccine reports with static CSS/fonts

### 11.4 Messages (i18n)

**File:** `src/presentation/messages/message_map.py`

`MessageMap` — i18n message map for Arabic/English. Used throughout CLI for user-facing messages.

---

## 12. Security & Licensing

### 12.1 License Guard

**File:** `src/infrastructure/security/license_guard.py`

`LicenseGuard` validates:
1. License file presence and integrity
2. Cryptographic signature (ECDSA-SHA256 with public key at `~/.cci_ft2/public.pem`)
3. Machine fingerprint tolerance (allows 1 component change)
4. Trial policy status (ACTIVE/EXPIRED/TAMPERED) — detects time rollback

**Usage:** Every use case calls `_guard.ensure_active()` before execution.

### 12.2 License Validator

**File:** `src/application/security/license_validator.py`

ECDSA-SHA256 signature verification for license files.

### 12.3 Trial Policy

**File:** `src/domain/policies/trial_policy.py`

Time-based trial license policy with clock-rollback detection.

**Key method:** `evaluate(current_time)` → `TrialStatus.ACTIVE/EXPIRED/TAMPERED`

**Trial duration:** 365 days (configured in `AppComposer._create_license_guard()`)

### 12.4 Encrypted License Repository

**File:** `src/infrastructure/security/encrypted_license_repository.py`

Encrypted license file storage at `~/.cci_ft2/license.dat`.

### 12.5 Fingerprint Provider

**File:** `src/infrastructure/security/fingerprint_provider.py`

`SystemFingerprintProvider` — Machine fingerprinting (machine ID, OS UUID, install timestamp).

### 12.6 File Lock Service

**File:** `src/application/services/file_lock.py`

Prevents concurrent processing of the same file using `filelock`. 30-second timeout.

---

## 13. Internationalization (i18n)

### 13.1 Language Manager

**File:** `src/shared/language_manager.py`

Singleton i18n manager with:
- Arabic/English fallback chain
- Arabic reshaping/bidi support
- Variable substitution
- Language loading from `src/shared/locales/`

### 13.2 Language Configuration

**Environment variable:** `CCI_LANG` — values: `ar` or `en` (default: `ar`)

### 13.3 Usage in Code

- CLI: Uses `MessageMap.get(key)` for user-facing messages
- GUI: Uses `lang.get(key)` with fallback to `_get_text(key)`
- Reports: Bilingual output (Arabic/English) in PDF reports

---

## 14. Testing Strategy

142 test files across multiple testing strategies:

| Test Category | Location | Purpose |
|---|---|---|
| **Unit** | `tests/unit/` | Domain entities, calculators, rules, DTOs, services, use cases, security, infrastructure adapters |
| **Integration** | `tests/integration/` | Full use case flows, ledger integrity, license, PDF fallback, VVM biological scenarios, concurrent writes, fingerprint tampering |
| **BDD** | `tests/bdd/` | Scenario-based tests (excursion device, safe device) |
| **Golden Master** | `tests/golden/` | PDF golden master, reference cold chain golden |
| **Architecture** | `tests/architecture/` | Layer separation, domain purity, dependency isolation, sealed domain layer |
| **Contracts** | `tests/contracts/` | Architecture contracts, domain invariants, PDF strategy contract, public contracts, time contract |
| **Regression** | `tests/regression/` | Scientific regression tests |
| **Performance** | `tests/performance/` | PDF generation speed benchmark |
| **Reporting** | `tests/reporting/` | Center report snapshot tests |
| **Fixtures** | `tests/fixtures/ft2/` | FT2 sample data (PDF and TXT) |

**Test tools:** pytest, pytest-mock, pytest-cov, pytest-xdist (parallel), pytest-benchmark, pytest-snapshot, pytest-env, pytest-timeout, freezegun

**Root conftest:** `conftest.py` — Adds project root to `sys.path` for import resolution.

**Running tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run architecture tests only
pytest tests/architecture/

# Run golden master tests
pytest tests/golden/

# Run with parallel execution
pytest -n auto
```

---

## 15. Configuration Management

### 15.1 Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `CCI_ENV` | Environment name | `development` |
| `CCI_DATA_ROOT` | Data root directory | — |
| `CCI_LOG_LEVEL` | Logging level | — |
| `CCI_LANG` | Language preference | `ar` |
| `CCI_ENABLE_SUPPLY_DATE` | Enable supply date filtering | — |
| `CCI_ENABLE_HEAT_DURATION` | Enable heat duration rule | — |
| `CCI_ENABLE_REFERENCE_AUDIT` | Enable scientific reference audit | — |

### 15.2 Config Files (`config/`)

| File | Purpose |
|---|---|
| `base.yaml` | App name, version, env, data_root, log_level, reporting defaults |
| `production.yaml` | Logging level, ledger path, auto-archive |
| `development.yaml` | Dev-specific settings |
| `testing.yaml` | Test-specific settings |
| `thresholds.yaml` | Safety thresholds (remaining_shelf_life_percentage: 50, fridgetag_alarm, flexible_vvm_allowed) |
| `center_profiles.yaml` | Center configuration profiles |
| `scientific_constants.yaml` | Scientific constants |
| `vaccine_library.yaml` | Vaccine library definitions |

### 15.3 Config Loader

**File:** `src/infrastructure/utils/config_loader.py`

`ConfigLoader` class with dot-notation access:
```python
ConfigLoader.get("thresholds.remaining_shelf_life_percentage", 50)
```

### 15.4 Shared Config

**File:** `src/shared/config.py`

`Config` class (singleton via `get_config()`):
- `env` (from `CCI_ENV`)
- `data_root` (from `CCI_DATA_ROOT`)
- `log_level` (from `CCI_LOG_LEVEL`)
- Feature flags: `CCI_ENABLE_SUPPLY_DATE`, `CCI_ENABLE_HEAT_DURATION`

### 15.5 LLM Configuration

**File:** `config.yaml` (root)

Configures Groq (Llama-3.1-8B) and Ollama models. Lists available free models.

---

## 16. Dependency Management

### 16.1 DI Container

**File:** `src/shared/di_container.py`

Lightweight, hand-rolled DI container supporting:
- `register(interface, implementation)` — Class registration
- `register_instance(interface, instance)` — Singleton registration
- `register_factory(interface, factory)` — Factory registration
- `resolve(interface)` — Resolution with automatic constructor injection (uses `inspect.signature`)

**DI usage rules** (enforced by `scripts/check_di_container_usage.py`):
- DI container may only be imported from **presentation layer** and **scripts**
- Domain and application layers must NOT import the container

### 16.2 App Composer (Composition Root)

**File:** `src/application/app_composer.py`

The primary composition root. Static factory methods build use cases with all dependencies wired.

**Note:** The `AppComposer` is the **only** place in the application layer that directly instantiates infrastructure adapters. All use cases receive interface-compliant dependencies.

---

## 17. CI/CD Pipeline

### 17.1 GitHub Actions Workflows (`.github/workflows/`)

| Workflow | Triggers | Key Steps |
|---|---|---|
| `ci.yml` | push to main/master/feature/*, PR to main/master | Two-stage: lite tests (no heavy deps) then full tests, pip-audit |
| `quality-gate.yml` | PR to main/develop, push to main | Sensitive hash verification, regression tests, architecture tests, Ruff lint, Black format check, Pylint |
| `security.yml` | PR/push | Bandit security scan on `src/` and `tests/` |
| `architectural-gate.yml` | push to main/develop, PR to main | Duplicate entity detection, architecture contract tests, layer boundary tests |
| `guard.yml` | same | Architecture guards |

### 17.2 Pre-commit Hooks (`.pre-commit-config.yaml`)

- JSON trailing spaces check
- JSON syntax validation
- Trailing whitespace fixer
- End-of-file fixer
- YAML check
- Merge conflict check
- Black formatting
- isort import ordering
- Bandit security scan

---

## 18. Key Design Patterns

### 18.1 Immutability by Default

- Most domain entities and value objects are `@dataclass(frozen=True)`
- DTOs are mostly frozen (9 immutable, 5 mutable out of 14 application DTOs)
- State transitions create new immutable copies rather than modifying existing state
- `ReportInputDTO` implements deep immutability via recursive `make_immutable()` (lists→tuples, dicts→MappingProxyType)

### 18.2 Fail-Fast Decision Cascade

`VaccineAssessmentService` uses sequential checks with immediate returns:
```
Expiry → VVM Stage → Circuit Breaker → CCM → HER
```
First matching condition determines the decision — no unnecessary computation.

### 18.3 Circuit Breakers

`ExposureAnalysisService._check_circuit_breakers()` provides instant DISCARD on:
- `FREEZE_EXCURSION` — temperature below freeze threshold
- `CRITICAL_HEAT_34C` — temperature above 34°C

### 18.4 Advisory vs Decision Separation

`ThermalDegradationEstimator` is explicitly marked as advisory-only and never influences decision paths. Decisions come from `RegulatoryDecisionService` or `VaccineAssessmentService`.

### 18.5 Protocol Pattern for Ports

Application layer defines interfaces as `Protocol` classes (e.g., `HerCalculatorService`, `CcmCalculatorService`) enabling pluggable implementations without coupling.

### 18.6 Null Object Pattern

`NoopReporterAdapter` implements report generator interface with no-op methods — used when reporting is not needed.

### 18.7 Feature Flags

Optional paths are gated behind environment variables:
- `CCI_ENABLE_SUPPLY_DATE` — supply date filtering
- `CCI_ENABLE_HEAT_DURATION` — heat duration rule
- `CCI_ENABLE_REFERENCE_AUDIT` — parallel scientific reference audit

### 18.8 Idempotency

`ManageFileLifecycleUseCase` uses SHA-256 hashing + `IFileRegistry` to prevent reprocessing. `FileLockService` prevents concurrent file processing.

### 18.9 Immutable Audit Ledger

`LedgerEntry` (in `src/domain/ledger/models.py`) is frozen and implements:
- SHA-256 hash computation
- Chain verification via `verify_chain(previous_hash)`
- Canonical JSON serialization (sorted keys, no spaces, primitive types only)

### 18.10 Fallback Field Access

Multiple services use `getattr()` chains for field name resilience:
```python
temp = getattr(reading, 'temperature', getattr(reading, 'temp', 0.0))
```

---

## 19. Known Technical Debt

### 19.1 Duplicate FileClassificationResult

`FileClassificationResult` exists in two locations:
- `src/application/dtos/file_classification_result.py`
- `src/application/ports/file_classification_result.py`

The `ssot_compliant` property has slightly different implementations between the two.

### 19.2 Unused PostgreSQL

`docker-compose.yml` defines a PostgreSQL service, but no Python code connects to it. All storage is file-based (JSON/YAML/JSONL/Parquet). This is scaffolding for future migration.

### 19.3 Stub Implementations

- `ImportFT2BundleUseCase._import_txt()` and `_import_pdf()` — stub implementations
- `ImportFT2BundleUseCase._log_to_ledger()` — stub
- `GenerateCenterReportUCPhase2` — not fully implemented (center report PDF returns empty bytes)
- `generate_all_device_reports` CLI command — stub ("coming in next release")
- GUI buttons: general data, units, vaccines, verify — all show "feature coming soon"

### 19.4 Legacy DTO Fields

`DeviceReportDTO` contains legacy fields alongside new fields:
- `vaccine_type: str` (legacy)
- `total_records: int` (legacy)
- `final_status: str` (legacy)
- `scientific_rationale: str` (legacy)

### 19.5 No HTTP API

Despite docker-compose exposing port 8000, there is no HTTP API framework in the codebase. This is likely planned but not yet implemented.

### 19.6 PATCH File in Domain Services

`src/domain/services/PATCH_VVMStageRule.py` — a patch file committed as source code. This suggests an incomplete refactoring of `VVMStageRule`.

---

## 20. How to Extend the System

### 20.1 Adding a New Calculator

1. Create calculator in `src/domain/calculators/`
2. Ensure it has zero imports from outer layers (run `python scripts/check_domain_purity.py`)
3. Write unit tests in `tests/unit/domain/calculators/`
4. If exposing via application layer, define a `Protocol` in `src/application/ports/`
5. Create adapter in `src/infrastructure/adapters/`

### 20.2 Adding a New Use Case

1. Create use case in `src/application/use_cases/`
2. Inherit from `BaseUseCase`
3. Implement `execute()` method
4. Define request/response DTOs in `src/application/dtos/` or in the use case file
5. Wire dependencies in `AppComposer`
6. Add CLI command in `src/presentation/cli/cli.py`
7. Write integration tests in `tests/integration/`

### 20.3 Adding a New Domain Entity

1. Create entity in `src/domain/entities/`
2. Prefer `@dataclass(frozen=True)` for immutability
3. Add validation in `__post_init__`
4. Write unit tests in `tests/unit/domain/entities/`
5. If needed, create a corresponding DTO in `src/application/dtos/`

### 20.4 Adding a New Rule

1. Create rule in `src/domain/rules/`
2. Inherit from `DecisionRule` (ABC)
3. Implement `evaluate()` method (or use `safe_evaluate()` for error handling)
4. Add rule to `RulesEngine` chain in correct order
5. Write tests in `tests/unit/domain/rules/`

### 20.5 Adding a New Vaccine Type

1. Add entry to `VACCINE_CATALOGUE` in `src/domain/value_objects/vaccine_specification.py`
2. Or add YAML spec file if using `YAMLVaccineSpecRepository`
3. Update tests in `tests/unit/domain/value_objects/test_vaccine_specification.py`

### 20.6 Running Architecture Guards

```bash
# Check domain purity (no outer layer imports in domain)
python scripts/check_domain_purity.py

# Check layer dependencies
python scripts/check_layer_dependencies.py

# Check project structure
python scripts/project_tree_guard.py

# Check DI container usage
python scripts/check_di_container_usage.py
```

### 20.7 Adding a New Infrastructure Adapter

1. Define interface (Port) in `src/application/ports/`
2. Create adapter in `src/infrastructure/adapters/`
3. Wire in `AppComposer`
4. Write adapter tests in `tests/unit/infrastructure/adapters/`
5. Write integration tests in `tests/integration/`

---

## Quick Reference: File-to-Responsibility Map

| Want to... | Look at... |
|---|---|
| Add a CLI command | `src/presentation/cli/cli.py` |
| Add a scientific calculator | `src/domain/calculators/` |
| Add a business rule | `src/domain/rules/` or `src/domain/services/rules_engine.py` |
| Add a use case | `src/application/use_cases/` + wire in `AppComposer` |
| Change PDF output | `src/presentation/reporting/` or `src/infrastructure/adapters/reporting/` |
| Change vaccine specs | `src/domain/value_objects/vaccine_specification.py` (catalogue) or `config/vaccine_library.yaml` |
| Change license behavior | `src/infrastructure/security/license_guard.py` |
| Add translations | `src/shared/locales/` |
| Add a domain entity | `src/domain/entities/` |
| Add a DTO | `src/application/dtos/` |
| Change storage | `src/infrastructure/adapters/json_*.py` or `src/infrastructure/repositories/` |
| Run tests | `pytest` from project root |
| Check architecture | `python scripts/check_domain_purity.py` |

---

*This document was generated by analyzing 73+ DTOs/models, 20 use cases, 12 domain services, 34 infrastructure adapters, and 142 test files. Last analyzed: April 13, 2026.*