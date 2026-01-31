# ADR0004 Implementation Summary

Date: 2026-01-31

Purpose
-------
This document summarises the minimal, auditable implementation performed to make ADR0004 verifiable and defensible.

What was done
--------------
- Converted `scripts/simple_pipeline.py` to use `CenterDTO` only and the composition root (`src/shared/di_container.py`).
- Migrated `scripts/run_ft2_pipeline.py` to create `CenterDTO` objects and used lightweight adapters for FT2 linking to avoid exporting Entities.
- Isolated `simulate_vvm_scenarios.py` into `tools/legacy/` with a LEGACY header and left a shim in `scripts/` to avoid accidental imports.
- Added a guard script `scripts/check_no_core_entity_imports.py` and CI workflow `.github/workflows/guard.yml` to fail PRs that import `src.core.entities` from protected paths.
- Added a contract test `tests/integration/test_no_entity_leak.py` that runs the guard script to ensure no leaks.

Why this approach
------------------
Small, reviewable PRs + an automated guard provide immediate architectural protection without a risky big-bang rewrite. This is consistent with the Charter and ADR0004's intent.

Evidence (local)
----------------
- Guard script output: OK on local run after changes.
- Files changed:
  - `scripts/simple_pipeline.py`
  - `scripts/run_ft2_pipeline.py`
  - `tools/legacy/simulate_vvm_scenarios.py`
  - `scripts/simulate_vvm_scenarios.py` (shim)
  - `scripts/check_no_core_entity_imports.py`
  - `.github/workflows/guard.yml`
  - `tests/integration/test_no_entity_leak.py`

Reviewer guidance
------------------
1. Review PR #1/PR #2/PR #3 for minimal changes — all changes are isolated and reversible.
2. Validate CI runs the guard and passes. The guard must remain enabled.
3. After merging, update ADR0004 with PR links and set `Status: Implemented`.

Next actions (recommended)
-------------------------
1. Merge PRs in sequence: PR #1, PR #2, PR #3.
2. Add one or two contract tests ensuring Use Cases cannot return Entities to outer layers.
3. Close ADR0004 and update `docs/ProjectState.md`.
