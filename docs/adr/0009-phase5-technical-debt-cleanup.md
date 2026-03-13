# ADR-0009: Phase 5 — Technical Debt Cleanup & Quality Hardening

Date: 2026-03-11
Status: Implemented

## Context

Following the successful completion of Phase 4 (Production Ready), a technical debt
cleanup phase was initiated to address accumulated issues identified during the
refactoring process. The codebase had several structural problems that needed
resolution before proceeding to new feature development.

### Problems Identified

1. **Dual wrapper files** for PDF generation with duplicated logic
2. **Duplicated DTOs** across `src/domain/dtos/` and `src/application/dtos/`
3. **Test coverage** at 78% — below the 85% target
4. **Legacy DI Container** (`src/shared/di_container.py`) coexisting with `AppComposer`
5. **Obsolete scripts and files** in root and scripts directory
6. **Missing imports** causing runtime errors (`List`, `Tuple` in `heat_exposure_engine.py`)
7. **AttributeError bug** in `vaccination_center.py` (`entry.temperature` vs `entry.temperatures`)

---

## Decisions

### 5.1 — ArabicFontManager Refactor

Introduced `src/infrastructure/pdf/arabic_font_manager.py` as the **single source
of truth** for all PDF generation logic.

- All classes unified: `ArabicFontManager`, `LegacyPDFGenerator`,
  `ArabicPDFGenerator`, `UnifiedPDFGeneratorWrapper`
- Font name constant unified: `ARABIC_FONT_NAME = "Amiri"`
- Both `unified_pdf_generator_wrapper.py` files converted to re-export shims
- Backward compatibility fully preserved (314 → 314 tests passing)

### 5.2 — DTO Source of Truth

`src/domain/dtos/` established as the **single source of truth** for all DTOs.

- All 7 files in `src/application/dtos/` converted to re-export shims
- Exception: `device_report_dto.py` kept in `application/` per architecture contract
  (`TestDTOSourceOfTruth.test_device_report_dto_single_source`)
- `src.domain.dtos` is now the canonical import path for all DTOs

### 5.3 — Coverage Improvement

Test coverage improved from **78% to 86%** (target was 85%).

New test files added:

| File | Coverage Target |
|------|----------------|
| `test_evidence_grade.py` | `EvidenceGrade` properties |
| `test_rules_engine_coverage.py` | `ExpiryRule`, `FreezeRule`, `HeatCriticalRule`, `ThawRule` |
| `test_exposure_mapper_and_dto.py` | `ExposureMapper`, `DeviceReportDTO`, Ports |
| `test_domain_calculators_entities.py` | `HERCalculator`, `Q10ThermalCalculator`, `FT2Entry` |
| `test_vaccination_center_coverage.py` | `VaccinationCenter` freeze/CCM logic |
| `test_domain_entities_engines.py` | `HeatExposure`, `DeviceReport`, `HeatExposureEngine` |

Bugs fixed during coverage work:
- `heat_exposure_engine.py`: missing `List`, `Tuple` imports
- `vaccination_center.py`: `AttributeError` — `entry.temperature` → safe fallback

### 5.4 — Documentation

- ADR-007 updated: Phase 4 implementation results added
- ADR-008 updated: Phase 5 implications section added
- ADR-009 (this document): Phase 5 complete record

### 5.5 — Dependency Wiring Review

`AppComposer` confirmed as the **only Composition Root**.

- `AppComposer.health_check()` returns `True`
- `src/shared/di_container.py` removed (163 lines of legacy DI)
- `src/presentation/cli/architectural_smoke_test.py` removed (marked for deletion since Phase 4)
- `patch_wrapper.py` removed (one-time patch script)
- `generate_plan.py` removed (obsolete planning document)
- `scripts/check_di_container_usage.py` removed
- `scripts/verify_phase3_fixes.py` removed

---

## Technical Debt Deferred to Phase 6

The following issues were identified but intentionally deferred:

### HER/CCM Protocol Incompleteness

`src/domain/services/her_calculator_service.py` contains `Protocol` definitions
for `HerCalculatorService` and `CcmCalculatorService` with stub implementations
(`Q10HerCalculator`, `TimeWeightedCcmCalculator`) that contain only `pass`.

These are **not wired** to any Use Case or AppComposer.

**Phase 6 action required:**
1. Implement `Q10HerCalculator.calculate()` with real Q10 formula
2. Implement `TimeWeightedCcmCalculator.calculate()` with time-weighted model
3. Wire both through `AppComposer`
4. Update `EvaluateColdChainSafetyUseCase` to use them

### Multiple PDF Generators in Presentation Layer

`src/presentation/reporting/` contains multiple PDF generators:
`arabic_pdf_generator.py`, `pdf_generator.py`, `professional_pdf_generator.py`,
`simple_pdf_generator.py`, `unified_pdf_generator.py`

**Phase 6 action required:** Consolidate into single entry point.

---

## Consequences

| Metric | Before Phase 5 | After Phase 5 |
|--------|---------------|--------------|
| Test Coverage | 78% | 86% |
| Tests Passing | 314 | 428 |
| Wrapper Files | 2 | 0 (re-exports) |
| DTO Duplication | 7 duplicate files | 0 (re-exports) |
| DI Systems | 2 (AppComposer + DIContainer) | 1 (AppComposer only) |
| Obsolete Files Removed | — | 6 files, ~1300 lines |
| Known Bugs Fixed | — | 2 |

The codebase is now in a clean state suitable for Phase 6 feature development.
