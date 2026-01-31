# Proposed Data Structure for Vaccine Profile with Q10 Support

This document outlines the proposed changes to the `vaccine_profiles` data structure to support the `VVMQ10Model`.

## Context

The existing `vaccine_profiles` in `config/center_profiles.yaml` define storage conditions and stability budgets. To integrate the new scientific model, we need to add properties specific to the Q10 calculation.

## Proposed YAML Structure

A new dictionary named `q10_properties` will be added to each relevant vaccine profile.

```yaml
- center_id: 130600112764
  center_type: "safe_hospital"
  short_name: "SAFE_HOSP"
  vaccine_profiles:
    - vaccine_name: "HEAT_SENSITIVE_VACCINE"
      storage_conditions:
        - condition_name: "Ideal"
          temperature_min: 2.0
          temperature_max: 8.0
      
      # NEW SECTION FOR VVM Q10 MODEL
      q10_properties:
        q10_value: 2.0  # The degradation rate multiplier for a 10°C temperature increase.
        ideal_temp: 5.0 # The reference 'ideal' temperature for Q10 calculations.
      
      stability_budgets:
        # ... existing stability budgets would remain here
```

### New Fields:

-   **`q10_properties`** (object): A container for all Q10 model-related parameters.
    -   **`q10_value`** (float, mandatory): The Q10 coefficient for the vaccine. It must be a positive number, typically in the range of 1.5 to 2.5.
    -   **`ideal_temp`** (float, mandatory): The ideal temperature (°C) that serves as the baseline for the Q10 calculation. When the actual temperature is at or below this value, the degradation acceleration factor is 1.0. This is often the midpoint of the ideal storage range.
