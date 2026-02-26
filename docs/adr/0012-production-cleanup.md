# ADR-0012: Production Cleanup and Test Hardening

**Date:** 2026-02-26  
**Status:** Accepted  
**Author:** Engineering Team

## Context

After successful production trial with real FT2 data (11 Ledger entries verified, audit passed), we identified structural cleanup needs before full production deployment.

## Problems Identified

1. **Weird files in src/**: `from pathlib import Path.ini`, `import subprocess`
2. **Duplicate Use Cases**: `evaluate_cold_chain_safety_uc.py` vs `_use_case.py`
3. **Duplicate documentation**: Multiple retrospective files
4. **Empty directories**: `data/processed`, `data/raw`, `data/reports`
5. **Test failures**: 7-9 tests failing due to outdated fixtures (not core functionality)
6. **DI Container pollution**: Mocks in production DI code

## Decision

### Phase 1: Clean Weird Files
- Delete `-H`, `-v`, `.coverage` from root
- Delete corrupted files in `src/application/ports/` and `src/domain/evidence/`
- Move test files from `src/` to `tests/`

### Phase 2: Consolidate Duplicates
- Keep single Use Case version (document removal)
- Merge duplicate documentation
- Document legacy tools with removal date

### Phase 3: Clean DI Container
- Remove all Mocks from production DI
- Use `_resolve_or_fail()` for strict dependency resolution
- Keep `build_generate_device_report_uc()` for production wiring only

### Phase 4: Test Hardening
- Update `HybridEvidenceValidator` fixtures with Fakes
- Fix `LicenseGuard` import path (`application.security` not `infrastructure.licensing`)
- Remove `data_path` from test calls or add as optional parameter

## Consequences

### Positive
- ✅ Cleaner codebase
- ✅ Reduced maintenance burden
- ✅ Clear production vs test boundaries
- ✅ 100% test pass rate target achievable

### Negative
- ⚠️ Temporary test failures during migration
- ⚠️ Need to update 7-9 test fixtures

### Risks
- ⚠️ Legacy removal may affect undocumented workflows
- ⚠️ Test fixture changes may reveal hidden dependencies

## Compliance

- ✅ Ledger integrity verified (11 entries)
- ✅ Hash chaining intact
- ✅ Audit passed
- ✅ Production data processing confirmed working

## Next Steps

1. Execute cleanup phases 1-4
2. Fix remaining 7-9 test failures
3. Run full test suite (target: 166/166 passing)
4. Tag v1.0.0-production-trial
5. Begin 90-day production trial
