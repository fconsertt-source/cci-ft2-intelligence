# API Reference

This document provides an overview of the project's public interface, including application use cases, ports, and key infrastructure entry points.

## Application Layer

- `src/application/use_cases/import_ft2_data_uc.py` - Use case for importing FT2 data into the domain.
- `src/application/use_cases/evaluate_cold_chain_safety_use_case.py` - Use case for evaluating cold chain safety from imported data.
- `src/application/use_cases/generate_device_report_uc_phase2.py` - Phase 2 use case for generating device-level reports.
- `src/application/use_cases/generate_center_report_uc_phase2.py` - Phase 2 use case for generating center-level reports.

## Ports

- `src/application/ports/i_report_generator.py` - Port interface for report generation adapters.
- `src/application/ports/i_ledger_service.py` - Port interface for ledger persistence and retrieval.
- `src/application/ports/i_license_guard.py` - Port interface for license validation.

## Infrastructure Layer

- `src/infrastructure/reporting/pdf_report_generator.py` - PDF report generation implementation.
- `src/infrastructure/ledger/ledger_service.py` - Ledger service implementation.
- `src/infrastructure/performance/performance_monitor.py` - Performance monitoring implementation.
- `src/infrastructure/security/license_guard.py` - License guard implementation.

## Scripts

- `scripts/migrate.py` - Migration wrapper entrypoint.
- `scripts/backup.py` - Backup wrapper entrypoint.
- `scripts/advanced_system_validation.sh` - Advanced validation harness for Phase 1/2 readiness.
