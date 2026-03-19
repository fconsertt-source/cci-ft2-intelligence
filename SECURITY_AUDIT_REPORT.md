# Security Audit Report - Contract Violations

## Critical Finding #1: Mock Pollution
- Tests use MagicMock instead of real VaccineSpecification
- Result: freeze_threshold_c = MagicMock (not -0.5)
- Impact: Freeze detection logic untested

## Critical Finding #2: Parameter Divergence  
- Tests assume max_heat_duration_hours = 2.0
- Production uses None (no limit)
- Impact: Heat excursion logic untested

## Critical Finding #3: Decision Engine Split
- Production: Uses both RulesEngine AND RegulatoryDecisionService
- Tests: Only test RegulatoryDecisionService with mocks
- Impact: RulesEngine completely untested!
