# ADR 0006: Migrate remaining scripts to DTO + centralized logging

Date: 2026-01-31

Status: accepted

Context
-------
Several utility and pipeline scripts under `scripts/` still used direct `print()` calls
and, in some cases, referenced Domain Entities at presentation boundaries. To comply with
the Engineering Charter we migrated these scripts to use:

- Centralized logging from `src.infrastructure.logging.get_logger()`
- Internal usage of Domain Entities (when necessary) with mapping to DTOs before any
  presentation or external output via mappers in `src.application.mappers`.

Files changed
-------------
- `scripts/project_utility.py`: replaced prints with `logger` and ensured `src` is importable.
- `scripts/create_test_data.py`: replaced prints with `logger` and added safe `src` import.
- `scripts/run_ft2_pipeline.py`: removed final print-summary in favor of logger; improved
  `device_map` construction to support DTOs and dict profiles; added `--generate-data` flag.
- `scripts/simulate_vvm_scenarios.py`: replaced prints with `logger`; scenarios still use
  internal `VaccinationCenter` entity and map to `CenterDTO` for display.
- `scripts/debug_ft2.py`: replaced final print with `logger` and ensured `src` import path.

Decision
--------
- Use `logger` for all script outputs so output can be configured centrally (handlers/levels).
- Keep Domain Entities internal to scripts that run the scientific/validation logic, but
  always map to DTOs before emitting presentation outputs.
- Prefer lazy imports for heavy reporting modules to keep test environments lightweight.

Consequences
------------
- Tests can run in minimal environments; heavy optional deps are imported lazily.
- Scripts now follow the Charter: DTOs + centralized logging + DI composition root.
- `run_ft2_pipeline.py` includes a safer `device_map` builder and a `--generate-data` flag for CI-friendly test data.
