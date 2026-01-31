# ADR0004 — Phase 3 Closure (Final)

Date: 2026-01-31

Status: Implemented

Summary
-------
This document records the final, auditable closure of ADR0004 (Phase 3: DTO + DI migration).

Links to evidence (replace placeholders with GH PR URLs after merge):

- PR #1 (Golden reference): <PR1_URL>
- PR #2 (Production migration): <PR2_URL>
- PR #3 (Legacy isolation): <PR3_URL>

What changed
------------
- `scripts/simple_pipeline.py` converted to DTO-only and wired via `src/shared/di_container.py`.
- `scripts/run_ft2_pipeline.py` migrated to construct `CenterDTO` objects and use adapter wrappers for linking.
- `simulate_vvm_scenarios.py` isolated into `tools/legacy/` (LEGACY tool); a shim remains in `scripts/` for discoverability.
- Added an automated guard `scripts/check_no_core_entity_imports.py` to prevent imports from `src.core.entities` in protected paths; enforced via `.github/workflows/guard.yml`.
- Contract test added: `tests/integration/test_no_entity_leak.py` which runs the guard during CI.

Why this satisfies ADR0004
-------------------------
- The migration enforces the Charter rule: Entities do not leave the Domain boundary.
- Changes were staged as minimal, reviewable PRs with automated enforcement to prevent regressions.
- The guard + contract test provide an automated, repeatable check that can be enforced via Branch Protection.

Operational next steps
----------------------
1. Merge PR#1 → PR#2 → PR#3 (order matters).  
2. Enable Branch Protection on `main` requiring the guard workflow and the tests contract to pass.  
3. Update this file by replacing `<PR1_URL>`, `<PR2_URL>`, `<PR3_URL>` with actual PR URLs and push.  
4. Update `docs/ProjectState.md` with the final project snapshot and note ADR0004 as implemented.

Signed-off-by: Architecture Team
