PRs and Git commands (ready to copy-paste)

Overview
--------
Three PRs, merged in order:

- PR#1: `feat/defense-simple-pipeline` — golden reference, includes guard + contract test + docs.
- PR#2: `feat/run-ft2-pipeline-dto` — production pipeline migration.
- PR#3: `feat/isolate-simulate-vvm-legacy` — legacy containment.

PR#1 — simple_pipeline (Golden reference)
-------------------------------------------------
Branch: feat/defense-simple-pipeline

Commands:
```
git checkout -b feat/defense-simple-pipeline
git add scripts/simple_pipeline.py docs/adr/0004-implementation-summary.md scripts/check_no_core_entity_imports.py .github/workflows/guard.yml tests/integration/test_no_entity_leak.py
git commit -m "Defense(PR#1): convert simple_pipeline to DTO-only; add guard, contract test, and implementation summary"
git push -u origin feat/defense-simple-pipeline
gh pr create --title "Defense: simple_pipeline → DTO-only + guard (PR#1)" --body "Goal: provide a golden reference proving ADR0004 is implementable. Changes: `scripts/simple_pipeline.py` (DTO-only), guard script, contract test, docs." --base main
```

Suggested PR body (short):
- Goal: Demonstrate ADR0004 is executable via a small, reviewable PR.
- What: `scripts/simple_pipeline.py` now builds and passes `CenterDTO` only; uses `create_evaluate_cold_chain_uc()` and centralized logging. Includes guard and contract test to make the ADR verifiable.
- Impact: Provides a golden reference for future migrations; prevents Entities leaking to scripts/presentation/reporting.

PR#2 — run_ft2_pipeline (Production path)
-------------------------------------------------
Branch: feat/run-ft2-pipeline-dto

Commands:
```
git checkout main
git pull origin main
git checkout -b feat/run-ft2-pipeline-dto
git add scripts/run_ft2_pipeline.py
git commit -m "Migration(PR#2): run_ft2_pipeline → produce CenterDTO; add adapters for FT2Linker"
git push -u origin feat/run-ft2-pipeline-dto
gh pr create --title "Migration: run_ft2_pipeline → DTO adapters (PR#2)" --body "Goal: migrate production pipeline to DTO-first pattern with minimal adapters to preserve runtime behavior." --base main
```

Suggested PR body (short):
- Goal: Move production pipeline to DTO-first with minimal behavioral change.
- What: `scripts/run_ft2_pipeline.py` now constructs `CenterDTO` objects and uses lightweight adapters so `FT2Linker` can add entries without exposing domain Entities outside the core.
- Impact: Protects architectural boundary at the primary entry point.

PR#3 — simulate_vvm_scenarios (Legacy isolation)
-------------------------------------------------
Branch: feat/isolate-simulate-vvm-legacy

Commands:
```
git checkout main
git pull origin main
git checkout -b feat/isolate-simulate-vvm-legacy
git add tools/legacy/simulate_vvm_scenarios.py scripts/simulate_vvm_scenarios.py
git commit -m "Containment(PR#3): isolate simulate_vvm_scenarios into tools/legacy (LEGACY shim kept in scripts/)"
git push -u origin feat/isolate-simulate-vvm-legacy
gh pr create --title "Containment: simulate_vvm_scenarios → tools/legacy (PR#3)" --body "Goal: contain legacy tooling outside protected paths. Moved to `tools/legacy/` and added a shim in `scripts/`." --base main
```

Suggested PR body (short):
- Goal: Isolate non-production tooling to avoid architectural leaks.
- What: Move `simulate_vvm_scenarios.py` into `tools/legacy/`; keep a shim in `scripts/` that points to the legacy tool.
- Impact: Removes the remaining entity import violations without deleting the tool.

Post-merge: Branch Protection (minimal)
-------------------------------------
1. In GitHub UI: Settings → Branches → Add rule for `main`.
2. Require status checks: add the guard workflow (name appears after first PR run) and the `tests` job (the pytest job name as shown in PR checks).
3. Optionally require pull request reviews before merging.

Notes
-----
- Do not add style/lint checks now; add as Phase-4.
- Ensure the exact status check names used in Branch Protection match the names shown in PR status contexts.
