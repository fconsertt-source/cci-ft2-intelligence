# ADR 0005: Migrate `scripts/simple_pipeline.py` to DTO + centralized logging

Date: 2026-01-31

Status: accepted

Context
-------
`scripts/simple_pipeline.py` is a lightweight pipeline script used for demos and local runs. Prior edits migrated several scripts to use `src.infrastructure.get_logger` and DTO/mappers. This ADR records the migration of `simple_pipeline.py` to the same pattern.

Decision
--------
- Replace top-level `print()` calls with `get_logger()` from `src.infrastructure.logging`.
- Keep a lightweight internal `CenterEntity` for processing; map to `CenterDTO` via `src.application.mappers.center_mapper.to_center_dto()` before any presentation or external output.
- Use lazy imports for heavy reporting modules to avoid import-time failures in minimal test environments.

Consequences
------------
- Tests can run without optional heavy dependencies (pandas/reportlab) because reporting imports are lazy and `verify_visual_reports.py` was adjusted.
- The pipeline now follows the Charter: entities remain internal and DTOs are used for presentation.
- Future refactors can replace `CenterEntity` with the project's canonical `VaccinationCenter` entity; mapping will remain stable at the DTO boundary.
