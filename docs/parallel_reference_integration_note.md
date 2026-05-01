# Parallel Reference Engine Integration Note

## Current cold-chain evaluation call flow
1. `EvaluateColdChainSafetyUseCase.execute()` receives `EvaluateColdChainSafetyRequest`.
2. `DomainCenterContext.from_request()` converts request readings into `TemperatureEntry` records with `duration_minutes`.
3. The legacy production path runs `ExposureAnalysisService().analyze(readings=ctx.ft2_entries, spec=request.vaccine_spec, supply_date=..., enable_supply_date=...)`.
4. Legacy analysis output is mapped into `extra_stats` with current operational keys:
   - `her_ratio`
   - `her`
   - `ccm_index`
   - `has_freeze`
   - `has_critical_heat`
   - `has_who_heat_exposure`
5. `apply_rules(ctx, extra_stats=extra_stats, enable_heat_duration=...)` merges those stats with `calculate_center_stats(ctx)` and sets:
   - `ctx.decision`
   - `ctx.vvm_stage`
   - `ctx.decision_reasons`
6. `JudgmentEngine.judge(...)` uses legacy operational values from the same legacy analysis result.
7. Final `stats = calculate_center_stats(ctx)` is updated with `extra_stats`, then `EvaluateColdChainSafetyResponse.from_context(ctx, stats)` returns the response.

## Safe injection point for parallel reference evaluation
Inject the reference path inside `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`, immediately after the existing legacy call to `ExposureAnalysisService().analyze(...)` and before rules/judgment assembly.

This is the safest point because:
- `ctx.ft2_entries` is already normalized.
- `request.vaccine_spec` is already available.
- The legacy operational path can remain unchanged.
- Reference outputs can be appended as telemetry/audit fields only.
- No existing rule or judgment contract must be rewritten in phase 1.

## Do not replace production logic
Phase-1 contract:
- Keep `ExposureAnalysisService` as the only source for:
  - `her_ratio`
  - `her`
  - `ccm_index`
  - `has_freeze`
  - `has_critical_heat`
  - `has_who_heat_exposure`
  - judgment inputs
  - decision-driving `extra_stats`
- The new reference engine must be read-only / audit-only.
- `ctx.decision`, `ctx.vvm_stage`, and `JudgmentEngine` inputs must continue to use legacy values only.
- No direct replacement of `ExposureAnalysisService` is allowed.

## Proposed new modules / files
Recommended additions only; no replacement of existing modules:

### Domain
- `src/domain/services/reference_exposure_analysis_service.py`
  - Main parallel scientific service.
  - Suggested method: `analyze(readings, spec, supply_date=None, enable_supply_date=False) -> dict`

### Domain adapter or mapping layer
- `src/domain/adapters/reference_analysis_adapter.py`
  - Maps reference result into a legacy-compatible telemetry payload without overriding legacy decision fields.
  - Suggested method: `to_extra_stats(reference_result: dict) -> dict`

### Infrastructure repository
- `src/infrastructure/repositories/yaml_vaccine_spec_repository.py`
  - YAML-backed SSOT reader for `config/vaccine_library.yaml`.
  - Should be additive and not force-cut existing JSON paths yet.
  - Suggested methods:
    - `get_vaccine_spec(vaccine_type: str)`
    - `get_defaults()`
    - `get_library_metadata()`

### Optional application orchestration helper
- `src/application/services/reference_reconciliation_service.py`
  - Compares legacy and reference outputs for audit / logging.
  - Suggested method:
    - `build_reference_extra_stats(legacy_analysis: dict, reference_analysis: dict) -> dict`

## Exact shared contracts

### Reference analysis service contract
Suggested public method name:
- `ReferenceExposureAnalysisService.analyze(...)`

Suggested payload shape:
- `reference_her_ratio: float`
- `reference_mkt_c: float | None`
- `reference_ccm_index: str | None`
- `reference_has_freeze: bool`
- `reference_has_critical_heat: bool`
- `reference_has_who_heat_exposure: bool`
- `reference_circuit_breaker: str | None`
- `reference_model_name: str`
- `reference_model_version: str`
- `reference_traceability_status: str | None`

### Adapter contract
Suggested public method name:
- `ReferenceAnalysisAdapter.to_extra_stats(reference_result: dict) -> dict`

Behavior:
- Return only namespaced keys for insertion into final `stats`.
- Must not emit unprefixed replacements for existing operational keys.

### Use case integration contract
Within `EvaluateColdChainSafetyUseCase.execute()`:
- Existing variable name `analysis` should remain the legacy result.
- New variable name should be explicit, e.g. `reference_analysis`.
- Existing `extra_stats` remains legacy decision input.
- Reference telemetry can be merged after legacy decision/judgment prep, e.g.:
  - `extra_stats.update(reference_extra_stats)`
- But reference keys must never overwrite legacy keys.

## Required `extra_stats` namespace
All new metrics added for the parallel reference path must use keys prefixed with `reference_`.

Approved examples:
- `reference_her_ratio`
- `reference_mkt_c`
- `reference_ccm_index`
- `reference_has_freeze`
- `reference_has_critical_heat`
- `reference_has_who_heat_exposure`
- `reference_circuit_breaker`
- `reference_model_name`
- `reference_model_version`
- `reference_traceability_status`
- `reference_delta_her_ratio`
- `reference_delta_ccm_index`
- `reference_alignment_status`

Not allowed in phase 1:
- Reusing `her_ratio` for reference values
- Reusing `ccm_index` for reference values
- Reusing `has_freeze` for reference values
- Any non-prefixed reference metric

## Repository / SSOT contract
Because `config/vaccine_library.yaml` exists and no repository currently exists at `src/infrastructure/repositories/yaml_vaccine_spec_repository.py`, the additive repository is a safe integration point.

Expected responsibility:
- Load vaccine defaults and per-vaccine records from `config/vaccine_library.yaml`
- Normalize lookup by vaccine type/code
- Provide data to the reference path without disturbing current production consumers

Important constraint:
- Do not remove or replace JSON/default-backed paths in phase 1.
- YAML repository should be introduced in parallel and consumed first by the new reference path.

## Notes on current architectural realities
- The current production use case imports domain services directly and uses dict-based result contracts.
- `apply_rules()` and `VVMStageRule` depend on legacy keys like `her_ratio` / `her`.
- `EvaluateColdChainSafetyResponse` does not currently expose reference fields directly, so phase-1 safest path is to keep reference outputs in final `stats` / audit plumbing only unless parent work later expands the response DTO.
- The repository path named in the task does not currently exist; creating it later is safe and additive.

## Minimal implementation sequence for later engineering
1. Add `ReferenceExposureAnalysisService`.
2. Add `YamlVaccineSpecRepository`.
3. Add `ReferenceAnalysisAdapter` that emits only `reference_*` keys.
4. Update `EvaluateColdChainSafetyUseCase.execute()` to:
   - run legacy analysis unchanged
   - run reference analysis in parallel
   - append `reference_*` telemetry into final stats
   - keep rules/judgment bound to legacy values only

## File ownership / integration summary for parent
This note defines the following shared names for downstream implementation:
- `ReferenceExposureAnalysisService.analyze(...)`
- `ReferenceAnalysisAdapter.to_extra_stats(...)`
- `YamlVaccineSpecRepository.get_vaccine_spec(...)`
- `YamlVaccineSpecRepository.get_defaults()`
- `YamlVaccineSpecRepository.get_library_metadata()`

And the mandatory namespacing rule:
- every added parallel-reference metric in `extra_stats` must start with `reference_`