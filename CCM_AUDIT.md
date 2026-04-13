## CCM Sources Audit

### Scope
This audit inspects the four active CCM-related sources requested:

1. `src/domain/services/exposure_analysis_service.py`
2. `src/domain/entities/ft2_entry.py`
3. `src/domain/calculators/ccm_calculator.py`
4. `src/domain/calculators/time_weighted_ccm_calculator.py`

It also traces `ccm` usage across `src/` and `tests/` to determine:
- the exact meaning of each CCM variant,
- whether it affects final decision logic,
- whether there is semantic conflict,
- and whether tests protect against that conflict.

---

## Phase 1 — Source-by-source findings

### Source 1: `ExposureAnalysisService`
**File:** `src/domain/services/exposure_analysis_service.py`

- **Definition:** WHO/PQS cumulative heat exposure classification.
- **Primary outputs:**
  - `ccm_index`
  - `total_hours_above_10`
  - `total_hours_above_34`
  - `has_critical_heat`
  - `has_ccm_violation`

#### What `_cumulative_hours_above()` returns exactly
`_cumulative_hours_above(readings, threshold)` returns the **total cumulative exposure time in hours** for readings whose temperature is strictly greater than the threshold.

Priority of duration extraction:
1. `duration_minutes` → converted to hours
2. `duration_hours`
3. pairwise `recorded_at` delta to the next reading
4. fallback default = `24.0` hours

#### How it handles the last reading
If the last reading is above the threshold and there is **no next reading**:
- if it has `duration_minutes`, that duration is used
- else if it has `duration_hours`, that duration is used
- else it falls back to **24.0 hours**

So the final reading can contribute a full default day if no explicit duration exists.

#### Default duration if all fields are absent
The default duration is **24.0 hours**.

This is true in both:
- `_get_duration_hours()`
- `_cumulative_hours_above()` for the final reading with no `next_reading`

#### Whether `has_ccm_violation == (hours_above_10 > 0)`
Yes. It is explicitly returned as:

```python
"has_ccm_violation": hours_above_10 > 0
```

This means **any positive exposure above 10°C**, even if very short and still within `ccm_index = "0"`, sets `has_ccm_violation=True`.

#### Unit
- cumulative exposure: **hours**

#### Thresholds
- above 10°C cumulative window
- above 34°C critical window
- `>= 2h above 34°C` → `D`

#### Output type
- `ccm_index`: categorical index (`0`, `A`, `AB`, `ABC`, `D`)
- `has_ccm_violation`: boolean

#### Used in final decision
**YES**

Evidence:
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py` passes:
  - `ccm_index`
  - `has_ccm_violation`
  - `has_critical_heat`
  into the decision flow.
- `src/domain/services/vaccine_assessment_service.py` also uses `ccm_index` directly.
- `src/domain/services/judgment_engine.py` uses `ccm_index`.
- `src/domain/entities/cooling_device.py` rejects on `ccm_index == "D"`.

---

### Source 2: `FT2Entry`
**File:** `src/domain/entities/ft2_entry.py`

- **Definition:** FT2 day-level alarm-derived CCM indicator based on `alarms["1"]["t_acc"]`.
- **Primary outputs:**
  - `has_ccm_violation`
  - `ccm_minutes`

#### What is the source of `alarms["1"]["t_acc"]`?
From this file **alone**, the value is not generated or normalized internally. It is consumed as raw input from the `alarms` structure:

```python
self.alarms.get("1", {}).get("t_acc", 0)
```

So in code terms:
- it comes from the FT2 entry payload / parsed FT2 data structure,
- not from a local calculation in `FT2Entry`.

This file strongly implies it is **raw FT2 alarm data**, but the file itself does **not** prove the physical device contract. It only proves this entity treats it as upstream raw input.

#### What is the unit of `t_acc`?
The code semantics indicate **minutes**.

Evidence:
- property name: `ccm_minutes`
- docstring: `"""دقائق CCM في هذا اليوم"""`
- threshold comparison: `> 600`
- test coverage also treats it as minutes

So the codebase treats `t_acc` as **minutes**, not seconds.

#### Why is the threshold `600`?
Inside this file there is **no regulatory citation** and no in-file rationale.

The number means:
- `600` minutes = `10` hours

But unlike `ExposureAnalysisService`, this file contains **no WHO/PQS reference** explaining why 600 is authoritative.

So:
- **code fact:** threshold is `600`
- **unit:** minutes
- **regulatory reference in this file:** **none**

#### Exact boolean logic
```python
return self.alarms.get("1", {}).get("t_acc", 0) > 600
```

This is a **strict greater-than** comparison, not `>= 600`.

#### Output type
- `has_ccm_violation`: boolean
- `ccm_minutes`: integer-ish raw minutes from source payload

#### Used in final decision
**INDIRECTLY / LEGACY YES**

Evidence:
- `src/domain/entities/vaccination_center.py` exposes:
  - `ccm_violations`
  - `total_ccm_minutes`
- `src/domain/services/rules_engine.py` uses a conceptually similar minutes-based rule:
  - `heat_duration > ccm_limit`
  - default `ccm_limit = 600`

However, the current main use case path in:
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py`

passes `has_ccm_violation` from `ExposureAnalysisService`, not from `FT2Entry`.

So `FT2Entry` semantics still exist in the model/reporting layer, but are **not the sole canonical source** in the newer decision path.

---

### Source 3: `CCMCalculator`
**File:** `src/domain/calculators/ccm_calculator.py`

- **Definition:** mathematical thermal metrics, not WHO index and not FT2 alarm minutes.
- **Primary outputs:**
  - `ccm_delta`
  - `ccm_auc`

#### `calculate_delta()`
Returns cumulative absolute temperature differences between consecutive readings when each difference is at least `threshold`.

This is a **temperature fluctuation metric**, not a WHO CCM index.

#### `calculate_auc()`
Returns trapezoidal area above a base temperature, using time deltas in **minutes**.

Unit is effectively:
- `(°C above base) × minutes` = **degree-minutes**

#### Is `calculate_delta()` or `calculate_auc()` called in the decision path?
From the `src/` audit:
- no evidence of any production decision path calling either function directly.
- grep finds the class definition and its own return fields, but no operational consumer in the main decision flow.

#### Dead code status
**Appears to be effectively isolated utility code / dead relative to final decision path.**

More precise wording:
- **Not proven dead globally**
- **Not proven live in final decision path**
- **Unit-tested, but no integration evidence into decision logic**

#### Used in final decision
**NO evidence**

---

### Source 4: `TimeWeightedCcmCalculator`
**File:** `src/domain/calculators/time_weighted_ccm_calculator.py`

- **Definition:** time-weighted thermal metrics returning a `CCMResult`.
- **Primary outputs:**
  - `ccm_delta`
  - `ccm_auc`
  - `total_duration_minutes`
  - `base_temp_used`
  - `readings_count`

#### Where is it called?
From the `src/` audit:
- no confirmed production caller in the final decision path
- grep shows only the class file and `CCMResult` object references, not a live pipeline consumer

#### Does it have tests?
**YES**

Covered by:
- `tests/unit/test_time_weighted_ccm_calculator.py`

#### Used in final decision
**NO evidence**

---

## Phase 2 — CCM usage inventory across `src/`

Search command used:

```bash
grep -rn --include="*.py" -i "ccm" src/
```

### Classification table

| File | Context | CCM type | Affects final decision? |
|------|---------|----------|--------------------------|
| `src/domain/services/exposure_analysis_service.py` | computes `ccm_index`, `total_hours_above_10`, `has_ccm_violation` | Index + hours-based boolean | YES |
| `src/application/use_cases/evaluate_cold_chain_safety_use_case.py` | forwards `ccm_index` and `has_ccm_violation` from analysis into rule flow | Index + boolean | YES |
| `src/domain/services/vaccine_assessment_service.py` | uses `ccm_index` to discard, especially `D` | Index | YES |
| `src/domain/services/judgment_engine.py` | uses `ccm_index` in confidence/narrative/risk | Index | YES |
| `src/domain/entities/cooling_device.py` | uses `ccm_index` and rejects on `D` | Index | YES |
| `src/domain/services/rules_engine.py` | uses `has_ccm_violation` based on `heat_duration > ccm_limit` | minutes / duration-threshold boolean | YES |
| `src/domain/rules/heat_exposure_rule.py` | rejects if `has_ccm_violation=True` | boolean, source-agnostic | YES |
| `src/domain/entities/ft2_entry.py` | exposes `has_ccm_violation` from `alarms["1"]["t_acc"] > 600` and `ccm_minutes` | raw FT2 minutes | INDIRECT / LEGACY YES |
| `src/domain/entities/vaccination_center.py` | aggregates `ccm_violations` and `total_ccm_minutes` from FT2 entries | raw FT2 minutes | INDIRECT |
| `src/application/services/center_stats_service.py` | computes `has_ccm_violation` from `heat_duration > 0` | duration-based boolean | YES, but conflicting logic |
| `src/presentation/reporting/csv_reporter.py` | reports `has_ccm_violation` | boolean | OUTPUT ONLY |
| `src/presentation/reporting/professional_pdf_generator.py` | reports `has_ccm_violation` | boolean | OUTPUT ONLY |
| `src/application/services/vaccines_report_generator.py` | includes `ccm_index` in report fields | Index | OUTPUT ONLY |
| `src/domain/calculators/ccm_calculator.py` | defines `ccm_delta` / `ccm_auc` calculators | delta / auc | NO evidence |
| `src/domain/calculators/time_weighted_ccm_calculator.py` | defines weighted `ccm_delta` / `ccm_auc` | delta / auc | NO evidence |
| `src/domain/value_objects/ccm_result.py` | result container for delta/auc metrics | delta / auc | NO evidence |
| `src/domain/services/her_calculator_service.py` | protocol references `CCMResult` / CCM calculator strategy | delta / auc abstraction | NO evidence |
| `src/application/dtos/evaluate_cold_chain_safety_request.py` | carries `has_ccm_violation`, `ccm_index` | boolean + index | transport only |
| `src/application/dtos/center_stats_dto.py` | carries `has_ccm_violation` | boolean | transport only |
| `src/domain/entities/heat_exposure.py` | contains field `ccm: float` | generic numeric CCM | unclear / not traced to decision |
| `src/domain/entities/vaccine_batch.py` | uses `cumulative_ccm` and sums `exp.ccm` | generic numeric cumulative CCM | not traced to decision |
| `src/infrastructure/adapters/json_vaccine_repository.py` | persists `ccm` and `cumulative_ccm` | generic numeric CCM | persistence only |

### Important note from inventory
There are not just two meanings of CCM. There are at least **four** active semantic families:

1. **WHO/PQS categorical index**
   - `ccm_index = 0 / A / AB / ABC / D`

2. **Any-above-threshold boolean**
   - `ExposureAnalysisService.has_ccm_violation = hours_above_10 > 0`

3. **Duration/minutes threshold boolean**
   - `FT2Entry.has_ccm_violation = t_acc > 600`
   - `RulesEngine.has_ccm_violation = heat_duration > ccm_limit`
   - `center_stats_service.has_ccm_violation = heat_duration > 0` ← another conflicting threshold

4. **Mathematical thermal metrics**
   - `ccm_delta`
   - `ccm_auc`
   - `cumulative_ccm`
   - `ccm: float`

So the semantic spread is broader than initially stated.

---

## Phase 3 — Test audit

Search basis:
- test audit produced in `tests/ccm_tests_audit.md`

### Coverage by source

| Source | Test coverage exists? | Notes |
|--------|------------------------|-------|
| `ExposureAnalysisService` | YES | strong direct tests for `ccm_index` thresholds |
| `FT2Entry` | YES | direct tests for `has_ccm_violation` and `ccm_minutes` |
| `CCMCalculator` | YES | direct unit tests + time unit contract |
| `TimeWeightedCcmCalculator` | YES | direct unit tests |

### Relevant test files
- `tests/unit/test_a1_exposure_analysis.py`
- `tests/unit/test_domain_calculators_entities.py`
- `tests/unit/test_ccm_calculator.py`
- `tests/contracts/test_time_contract.py`
- `tests/unit/test_time_weighted_ccm_calculator.py`
- decision-path related:
  - `tests/unit/test_rules_logic.py`
  - `tests/unit/test_rules_engine_coverage.py`
  - `tests/unit/application/use_cases/test_evaluate_cold_chain_safety_use_case.py`
  - `tests/unit/test_b4_vaccine_pipeline_integration.py`

### Does any test prove alignment between `ExposureAnalysisService` and `FT2Entry`?
**NO**

No test was found that:
- constructs equivalent heat exposure,
- maps corresponding FT2 `alarms["1"]["t_acc"]`,
- and asserts agreement or intentional disagreement.

### Does any test expose the semantic conflict?
**NO**

Current suite does not explicitly protect against:

- `ExposureAnalysisService.has_ccm_violation == True` for **any** exposure above 10°C
versus
- `FT2Entry.has_ccm_violation == True` only when `t_acc > 600`

### Coverage conclusion
All four definitions are individually tested, but the suite does **not** test their interoperability or consistency.

---

## Conflict Summary

### Core naming conflict
The same field name:

```python
has_ccm_violation
```

means different things in different parts of the codebase:

#### Meaning A — `ExposureAnalysisService`
```python
has_ccm_violation = hours_above_10 > 0
```
Meaning:
- any positive exposure above 10°C
- unit basis: **hours**
- threshold: effectively **> 0**

#### Meaning B — `FT2Entry`
```python
has_ccm_violation = alarms["1"]["t_acc"] > 600
```
Meaning:
- FT2 accumulated alarm minutes exceed 600
- unit basis: **minutes**
- threshold: **> 600 minutes**

#### Meaning C — `RulesEngine`
```python
has_ccm_violation = heat_duration > ccm_limit
```
Meaning:
- heat duration exceeds configured threshold
- default threshold: **600 minutes**

#### Meaning D — `center_stats_service`
```python
has_ccm_violation = any(getattr(e, "heat_duration", 0) > 0 for e in entries_list)
```
Meaning:
- any heat duration > 0
- effectively a different boolean again

### Risk
This creates a high-risk semantic collision:

- identical field name,
- incompatible thresholds,
- incompatible units,
- mixed raw device semantics and analytical semantics,
- and decision/reporting layers consuming the same name as though it were canonical.

### Practical failure mode
The same real-world dataset can yield:

- `ccm_index = "0"`  
- `ExposureAnalysisService.has_ccm_violation = True`  
- `FT2Entry.has_ccm_violation = False`

This is not hypothetical; it follows directly from current thresholds:

- exposure above 10°C for, say, 30 minutes:
  - above-10 hours > 0 → `True`
  - still below 72 hours → `ccm_index = "0"`
  - still below 600 minutes → FT2 boolean `False`

So one field name currently conflates:
- **any exposure**
- **threshold breach**
- **device alarm accumulation**
- **WHO classification state**

---

## Decision answers requested

| Question | Answer | Decision implication |
|----------|--------|----------------------|
| Is `CCMCalculator` dead code? | Not provably dead globally, but no evidence it participates in final decision path | treat as isolated/experimental until proven otherwise |
| Is `TimeWeightedCcmCalculator` in final decision path? | No evidence | treat as isolated analytical utility |
| Is `t_acc` trusted FT2 source data? | It is treated as raw upstream FT2 alarm data by `FT2Entry`, but this file alone does not prove the hardware contract | use as raw device source only after documenting upstream provenance |
| Is `t_acc` in minutes? | Yes, by code semantics | safe to document as minutes in current code |
| Does `FT2Entry` justify `600` with regulatory reference? | No | threshold must be documented externally or renamed as device-policy threshold |
| Is `has_ccm_violation` semantically conflicting? | Yes, severely | one of the meanings should be renamed immediately |
| Do tests cover the conflict? | No | add an integration test that demonstrates divergence |

---

## Recommended immediate renames

### Keep separate names for separate meanings
Suggested direction:

- `ExposureAnalysisService.has_ccm_violation`
  - rename to something like:
    - `has_any_exposure_above_10c`
    - or `has_who_heat_exposure`

- `FT2Entry.has_ccm_violation`
  - rename to something like:
    - `has_ft2_ccm_alarm`
    - or `has_ft2_tacc_violation`

- `RulesEngine` boolean
  - rename to something like:
    - `has_heat_duration_limit_breach`

- keep `ccm_index` only for WHO/PQS categorical result

- keep `ccm_delta` / `ccm_auc` only for analytical metric objects, never decision booleans

---

## Recommended missing tests

### 1) Semantic conflict integration test
Add one test proving:

- exposure above 10°C for less than 72h:
  - `ccm_index == "0"`
  - `ExposureAnalysisService.has_ccm_violation == True`
  - `FT2Entry.has_ccm_violation == False` when `t_acc <= 600`

This test should exist specifically to prevent silent semantic merging.

### 2) Boundary test for FT2Entry
Add exact-threshold test:

- `t_acc == 600` → should remain `False`

### 3) Direct assertion for ExposureAnalysisService boolean
Add test asserting:

- if `hours_above_10 > 0`, then `has_ccm_violation == True`

and separately show this can coexist with `ccm_index == "0"`.

---

## Bottom line

The codebase currently uses **CCM** to mean multiple incompatible things:

1. WHO/PQS heat exposure category (`ccm_index`)
2. any-above-10°C exposure boolean
3. FT2 raw accumulated alarm minutes
4. duration-threshold boolean in legacy rules
5. mathematical delta/AUC thermal metrics
6. generic numeric cumulative CCM fields in other entities

The most dangerous collision is the shared field name:

```python
has_ccm_violation
```

which currently means different things depending on the source.

This should be treated as a **semantic integrity bug**, not just a naming inconsistency.
