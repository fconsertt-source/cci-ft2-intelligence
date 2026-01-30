# Cold Chain Safety Decision Matrix

This document explains how the **Rules Engine** makes decisions about vaccine safety.

## 1. Priority-Based Architecture

Decisions are made using a **Chain of Responsibility** pattern. Rules are evaluated in the following order. The first rule to trigger a decision becomes the final outcome.

| Priority | Rule Name | Trigger Condition | Outcome | Impact |
| :--- | :--- | :--- | :--- | :--- |
| 0 | **ExpiryRule** | Current Date > `expiry_date` | `REJECTED_EXPIRED` | Critical |
| 1 | **VVMStageRule** | `HER >= 1.0` (Stage D) | `REJECTED_HEAT_C` | Biological (Q10) |
| 2 | **FreezeRule** | Temperature < 0°C (if sensitive) | `REJECTED_FREEZE` | Zero Tolerance |
| 3 | **HeatCriticalRule** | Temp > `critical_limit` OR CCM Violated | `REJECTED_HEAT_C` | Threshold |
| 4 | **WarningRule** | Temp outside [2°C, 8°C] | `ACCEPTED` (with Warning) | Monitoring |
| 5 | **DefaultRule** | No other rules triggered | `ACCEPTED` | Safe |

## 2. VVM Stage Transitions (Scientific Model)

The `VVMStageRule` uses the **Heat Exposure Ratio (HER)** calculated by the `VVMQ10Model`.

| HER Range | VVM Stage | Description | Final Status |
| :--- | :--- | :--- | :--- |
| < 0.1 | **NONE** | No significant degradation. | SAFE |
| 0.1 - 0.4 | **Stage A** | Early degradation started. | SAFE/PARTIAL |
| 0.4 - 0.7 | **Stage B** | Noticeable degradation. | PARTIAL |
| 0.7 - 1.0 | **Stage C** | Near end of life. Use immediately. | PARTIAL |
| >= 1.0 | **Stage D** | **Discard.** Potency loss. | DISCARD |

## 3. CCM vs. Q10

- **CCM (Cold Chain Monitor):** A linear accumulation of minutes above 8°C. Used as a safety "buffer" or legacy threshold.
- **Q10 (Scientific Model):** An exponential model based on biochemical kinetics. Used for precise shelf-life estimation.

## 4. Status Mapping

In the application layer (`EvaluateColdChainSafetyUC`), string decisions are mapped to `VaccineStatus` enums:

- `ACCEPTED` -> `SAFE` (or `PARTIAL` if warnings/VVM stages exist)
- `REJECTED_*` -> `DISCARD`
