# Reference Exposure Analysis Discovery

## Scope inspected
- `src/domain/services/exposure_analysis_service.py`
- `src/domain/services/vaccine_assessment_service.py`
- `src/domain/services/rules_engine.py`
- `src/domain/calculators/q10_her_calculator.py`
- `src/domain/value_objects/her_result.py`
- `src/domain/value_objects/ccm_result.py`
- `src/domain/value_objects/vaccine_specification.py`
- `src/domain/value_objects/temperature_entry.py`
- `src/domain/entities/temperature_reading.py`
- `src/domain/models/temperature_exposure.py`
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`
- `src/application/dtos/evaluate_cold_chain_safety_request.py`
- `src/application/mappers/exposure_mapper.py`
- `SYSTEM_HANDOFF.md`

## Current layering observations

### Best current domain home
`src/domain/services/exposure_analysis_service.py` is the current scientific orchestration point. It already:
- accepts readings plus `VaccineSpecification`
- computes HER, CCM-like window status, freeze, critical heat
- returns the exact dict shape consumed by application and rules

A new parallel path should therefore live beside it in the same layer, not in application and not in infrastructure.

### Safe candidate file paths
Primary candidate:
- `src/domain/services/reference_exposure_analysis_service.py`

Optional typed result contract if implementation later needs stricter shape without disturbing legacy dict consumers:
- `src/domain/value_objects/reference_exposure_analysis_result.py`

Optional adapter at application boundary if parent agent wants mapping isolated from use case:
- `src/application/adapters/reference_analysis_result_adapter.py`

Given current project structure, the lowest-risk first move is:
1. add `src/domain/services/reference_exposure_analysis_service.py`
2. keep output mapping in a thin adapter/helper near the use case boundary
3. preserve existing `ExposureAnalysisService` untouched

## Existing DTOs/models to reuse

### Reuse as input models
1. `src/domain/value_objects/temperature_entry.py`
   - fields: `temperature`, `timestamp`, `duration_minutes`, `device_id`
   - this is the real input shape currently built by `EvaluateColdChainSafetyUseCase`
   - best reusable input for a reference service if we want zero extra conversion in the use case

2. `src/domain/entities/temperature_reading.py`
   - fields: `value`, `recorded_at`, `duration_hours`, `device_id`, `location`
   - useful only if a reference engine wants the entity-oriented pairwise/Q10 style already used by `Q10HerCalculator`

3. `src/domain/value_objects/vaccine_specification.py`
   - should remain the vaccine/spec contract passed to any reference service
   - contains all needed scientific fields:
     - `q10_factor`
     - `shelf_life_days` / `shelf_life_hours`
     - `reference_temp_c`
     - `freeze_sensitive`
     - `critical_temp_c`
     - `critical_hours`
     - legacy compatibility fields such as `max_heat_duration_hours`

### Reuse as sub-result types
1. `src/domain/value_objects/her_result.py`
   - strong candidate for encapsulating reference HER output internally

2. `src/domain/value_objects/ccm_result.py`
   - less aligned with current legacy `ccm_index` contract, but useful if the reference path computes typed cumulative heat metrics internally

3. `src/domain/models/temperature_exposure.py`
   - useful if reference engine wants pure `temperature + duration_minutes` segments
   - already supported by `src/application/mappers/exposure_mapper.py`
   - however current use case already constructs `TemperatureEntry`, so this is secondary reuse

## Current result contract that must remain compatible

### Legacy analysis dict contract
`ExposureAnalysisService.analyze()` returns a dict with keys:
- `her_ratio`
- `ccm_index`
- `has_freeze`
- `has_critical_heat`
- `max_temp`
- `min_temp`
- `total_hours_above_10`
- `total_hours_above_34`
- `circuit_breaker`
- `data_quality_flags`
- `has_who_heat_exposure`

### Application consumption points
`src/application/use_cases/evaluate_cold_chain_safety_use_case.py` consumes:
- `her_ratio`
- `ccm_index`
- `has_freeze`
- `has_critical_heat`
- `has_who_heat_exposure`

It then builds `extra_stats` and passes them to:
- `apply_rules(...)` in `src/domain/services/rules_engine.py`
- `JudgmentEngine.judge(...)` in `src/domain/services/judgment_engine.py`

### Important constraint for the reference path
Per project contract, new extra stats must be namespaced with `reference_`. So reference outputs should not overwrite:
- `her_ratio`
- `ccm_index`
- `has_freeze`
- `has_critical_heat`

Instead they should be mapped to additive keys such as:
- `reference_her_ratio`
- `reference_ccm_index`
- `reference_has_freeze`
- `reference_has_critical_heat`
- `reference_max_temp`
- `reference_min_temp`
- `reference_total_hours_above_10`
- `reference_total_hours_above_34`
- `reference_circuit_breaker`
- `reference_has_who_heat_exposure`
- `reference_sampling_gap`
- `reference_engine_version`

## Recommended adapter shape

### Domain service API
Suggested method:
- `ReferenceExposureAnalysisService.analyze(readings, spec=None, supply_date=None, enable_supply_date=False) -> dict`

Reason:
- identical signature to `ExposureAnalysisService.analyze`
- easiest parallel invocation from the use case
- avoids new conversion burden
- makes A/B comparison trivial

### Adapter/helper responsibility
Map reference raw output into additive stats only.

Suggested helper contract:
- `adapt_reference_analysis_to_extra_stats(reference_analysis: dict) -> dict`

Suggested output keys:
- `reference_her_ratio`
- `reference_ccm_index`
- `reference_has_freeze`
- `reference_has_critical_heat`
- `reference_max_temp`
- `reference_min_temp`
- `reference_total_hours_above_10`
- `reference_total_hours_above_34`
- `reference_circuit_breaker`
- `reference_has_who_heat_exposure`
- `reference_sampling_gap`

Optional comparison keys, also prefixed:
- `reference_delta_her_ratio`
- `reference_matches_freeze_flag`
- `reference_matches_ccm_index`

## Integration point without violating layering

### Best injection site
Inside `EvaluateColdChainSafetyUseCase.execute()` after current legacy analysis is computed:

1. keep current call:
   - `analysis = ExposureAnalysisService().analyze(...)`
2. invoke parallel reference service:
   - `reference_analysis = ReferenceExposureAnalysisService().analyze(...)`
3. map only additive namespaced fields into `extra_stats`
4. continue using current production path for:
   - `apply_rules`
   - `JudgmentEngine`
   - response decision fields

This preserves operational behavior while exposing comparison telemetry.

### Why not inside rules engine
`rules_engine.py` expects production stats and drives the final decision. Injecting reference logic there would risk accidental behavioral replacement.

### Why not infrastructure
The scientific calculation is domain logic, not IO/integration logic.

## Reuse notes for future implementation
- If reference implementation needs pure exposure segments, convert `TemperatureEntry` to `TemperatureExposure` in application or inside the new domain service, but do not replace existing `DomainCenterContext`.
- If reference implementation needs typed HER internals, compose `Q10HerCalculator` and adapt its `HERResult` back to the legacy-compatible dict.
- If a typed result object is later introduced, keep a `.to_legacy_dict()` or adapter path so the use case remains minimally changed.

## Risks found
1. `ExposureAnalysisService` currently returns untyped dicts, so downstream code depends on literal key names.
2. There are two `JudgmentEngine` implementations:
   - `src/domain/services/judgment_engine.py`
   - `src/application/services/judgment_engine.py`
   The use case imports the domain one, so any new adapter should not assume the application one is active.
3. `ExposureAnalysisService` references `timezone` inside supply-date logic but the visible import section only includes `datetime`; this is an existing issue to avoid touching during discovery.
4. Current use case has debug `print(...)` calls; reference integration should avoid adding more stdout noise.

## Recommended next-step contract for parent/other agents
- New service file: `src/domain/services/reference_exposure_analysis_service.py`
- Optional adapter file: `src/application/adapters/reference_analysis_result_adapter.py`
- Shared method name: `analyze(...)`
- Shared additive stats keys must all start with `reference_`
- No direct replacement of `ExposureAnalysisService`
- No rule/decision switching based on reference output in first phase