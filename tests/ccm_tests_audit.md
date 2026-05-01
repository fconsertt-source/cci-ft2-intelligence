# CCM Tests Audit

## Scope
- Reviewed CCM definitions in:
  - `src/domain/services/exposure_analysis_service.py`
  - `src/domain/entities/ft2_entry.py`
  - `src/domain/calculators/ccm_calculator.py`
  - `src/domain/calculators/time_weighted_ccm_calculator.py`
- Searched `tests/` for:
  - `ccm`, `CCM`, `has_ccm_violation`, `ccm_index`, `ccm_delta`, `ccm_auc`, `ccm_minutes`, `t_acc`

## Relevant test files and coverage

### 1) `ExposureAnalysisService`
**Relevant files**
- `tests/unit/test_a1_exposure_analysis.py`
- Indirect/decision-path usage:
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py`
  - `tests/unit/test_b4_vaccine_pipeline_integration.py`

**Coverage type**
- Strong direct unit coverage in `test_a1_exposure_analysis.py`:
  - `ccm_index` thresholds:
    - `0` for `<72h above 10°C`
    - `A` for `72–192h`
    - `AB` for `192–336h`
    - `ABC` for `>=336h`
    - `D` for `>=2h above 34°C`
  - `total_hours_above_10`
  - `has_critical_heat`
  - circuit breaker interaction with CCM D
- Indirect integration evidence:
  - `tests/unit/test_b4_vaccine_pipeline_integration.py` proves downstream discard on `ccm_index == "D"` in vaccine assessment pipeline.
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py` checks returned `has_ccm_violation` for a safe scenario only.

**Gaps**
- No direct assertion in `test_a1_exposure_analysis.py` for `has_ccm_violation = hours_above_10 > 0`.
- No test explicitly checks the semantic mismatch between:
  - `ccm_index == "0"` with some exposure above 10°C but less than 72h
  - `has_ccm_violation == True` for the same case
- No explicit test for `total_hours_above_34` field.
- No test that compares ExposureAnalysisService output against FT2Entry output on the same logical scenario.

---

### 2) `FT2Entry`
**Relevant file**
- `tests/unit/test_domain_calculators_entities.py`

**Coverage type**
- Direct unit coverage exists for:
  - `has_ccm_violation` true when `alarms["1"]["t_acc"] > 600`
  - `has_ccm_violation` false at default zero
  - `ccm_minutes`
  - raw `t_acc` plumbing through `alarms`

**What is covered exactly**
- `test_has_ccm_violation_true`
- `test_has_ccm_violation_false`
- `test_ccm_minutes`
- tests use `alarms={"1": {"t_acc": ...}}` directly

**Gaps**
- No boundary test for exactly `t_acc == 600` to confirm strict `>` semantics.
- No cross-check with ExposureAnalysisService semantics.
- No integration test proving that FT2Entry-based CCM status aligns with decision engine output.

---

### 3) `CCMCalculator`
**Relevant files**
- `tests/unit/test_ccm_calculator.py`
- `tests/contracts/test_time_contract.py`

**Coverage type**
- Strong direct unit coverage in `tests/unit/test_ccm_calculator.py`:
  - `calculate_delta_minutes`
  - `calculate_delta`
  - `calculate_auc`
  - sorting behavior
  - custom threshold
  - custom base temperature
  - `calculate()` result shape with `ccm_delta`, `ccm_auc`, `method_used`
- Contract coverage in `tests/contracts/test_time_contract.py`:
  - `TIME_UNIT == "minutes"`

**Gaps**
- No integration test showing `CCMCalculator` is used in final decision flow.
- Based on tests alone, it appears isolated/unit-tested utility logic, not proven decision-path logic.

---

### 4) `TimeWeightedCcmCalculator`
**Relevant file**
- `tests/unit/test_time_weighted_ccm_calculator.py`

**Coverage type**
- Strong direct unit coverage for:
  - empty/single input
  - duplicate timestamps
  - AUC correctness
  - total duration
  - `auc_per_hour`
  - `has_heat_exposure`
  - `ccm_delta`
  - ordering invariance
  - independence from HER imports

**Gaps**
- No integration test showing it is consumed by decision flow, use case, or report path.
- No evidence in tests that its `CCMResult` fields affect final vaccine or center decisions.

---

## Decision-path related tests inside `tests/`
These do not test the four definitions directly, but they show which CCM-style fields are actually consumed in decision rules:

### Rules/decision tests
- `tests/unit/test_rules_logic.py`
- `tests/unit/test_rules_engine_coverage.py`
- `tests/unit/domain/rules/test_heat_exposure_rule.py` (found by grep output)

**What they validate**
- Decision logic consumes `has_ccm_violation`
- When `has_ccm_violation=True`, heat rejection occurs
- These tests operate on prepared stats/mocks, not on real `ExposureAnalysisService` + `FT2Entry` side-by-side

### Reporting/snapshots
- snapshot TSV/ambr files include `has_ccm_violation`
- This is output-schema evidence, not semantic validation

---

## Integration evidence: ExposureAnalysisService vs FT2Entry
**Result: no integration evidence found**

There is **no test** in `tests/` that:
- feeds equivalent heat exposure into `ExposureAnalysisService`
- maps equivalent FT2 `alarms["1"]["t_acc"]`
- then asserts they agree or intentionally differ on `has_ccm_violation`

Also not found:
- any scenario explicitly demonstrating the semantic conflict:
  - `ExposureAnalysisService.has_ccm_violation` becomes `True` for any `hours_above_10 > 0`
  - `FT2Entry.has_ccm_violation` becomes `True` only for `t_acc > 600` minutes

This means the suite does **not** currently protect against disagreement between:
- “any above-10 exposure”
- “more than 600 accumulated CCM minutes”

---

## Summary
- `ExposureAnalysisService`: **covered directly**, especially `ccm_index`; but `has_ccm_violation` semantic is **not directly asserted**.
- `FT2Entry`: **covered directly** for `has_ccm_violation`, `ccm_minutes`, and `t_acc` mapping.
- `CCMCalculator`: **well unit-tested** and `TIME_UNIT` contract-tested, but **no integration evidence** into final decision path.
- `TimeWeightedCcmCalculator`: **well unit-tested**, but **no integration evidence** into final decision path.
- **No test** proves alignment between `ExposureAnalysisService` and `FT2Entry`.
- **No test** explicitly exposes their current semantic mismatch.