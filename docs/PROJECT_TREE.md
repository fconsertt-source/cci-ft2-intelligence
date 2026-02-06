```tree
└── cci-ft2-intelligence
    ├── -H
    ├── .continue
    │   └── agents
    │       ├── new-config-1.yaml
    │       └── new-config.yaml
    ├── .github
    │   └── workflows
    │       └── guard.yml
    ├── .gitignore
    ├── .qodo
    │   ├── agents
    │   └── workflows
    ├── assets
    │   └── fonts
    ├── backup
    │   ├── backup_20260131_000840.tar.gz
    │   └── backup_20260203_171607.tar.gz
    ├── config
    │   ├── __init__.py
    │   ├── center_profiles.yaml
    │   ├── center_profiles_enhanced.yaml
    │   ├── ci_guard.yml
    │   ├── system_config.yaml
    │   ├── templates
    │   ├── thresholds.yaml
    │   └── vaccine_library.yaml
    ├── config.yaml
    ├── conftest.py
    ├── data
    │   ├── __init__.py
    │   ├── archive
    │   ├── input_ft2
    │   │   ├── 130600112764_202201241939.txt
    │   │   ├── __init__.py
    │   │   ├── freeze_clinic_130600112767.txt
    │   │   ├── heat_mobile_130600112769.txt
    │   │   └── safe_hospital_130600112764.txt
    │   ├── input_raw
    │   │   ├── __init__.py
    │   │   ├── freeze_clinic_130600112767.csv
    │   │   ├── heat_mobile_130600112769.csv
    │   │   ├── safe_hospital_130600112764.csv
    │   │   └── test_data.csv
    │   ├── output
    │   │   ├── __init__.py
    │   │   ├── detailed_reports
    │   │   │   ├── report_001.txt
    │   │   │   ├── report_002.txt
    │   │   │   ├── report_003.txt
    │   │   │   └── report_004.txt
    │   │   ├── reports
    │   │   └── visual_tests
    │   │       ├── mock_visual_data.tsv
    │   │       ├── temp_dist.png
    │   │       ├── visual_test_arabic.pdf
    │   │       ├── visual_test_official.pdf
    │   │       └── visual_test_tech.pdf
    │   ├── processed
    │   ├── raw
    │   └── reports
    ├── docs
    │   ├── __init__.py
    │   ├── adr
    │   │   ├── 0001-adopt-structure.md
    │   │   ├── 0003-phase2-findings.md
    │   │   ├── 0004-final-closure.md
    │   │   ├── 0004-implementation-summary.md
    │   │   ├── 0004-phase3-plan.md
    │   │   ├── 0005-architecture-lockdown.md
    │   │   ├── 0005-simple-pipeline-migration.md
    │   │   ├── 0006-scripts-migration.md
    │   │   ├── 0007-introduce-application-ports-and-composition-root.md
    │   │   ├── 0008-completion-of-pure-use-case-migration.md
    │   │   └── 0009-presentation-boundary-lock.md
    │   ├── architecture
    │   │   ├── __init__.py
    │   │   ├── DECISION_MATRIX.md
    │   │   └── ENGINEERING_CHARTER.md
    │   ├── Clean_Architecture_Project.md
    │   ├── decision_matrix.md
    │   ├── phase-a-hardened-architecture-plan.md
    │   ├── project-retrospective.md
    │   ├── project_state_manifest.json
    │   ├── PROJECT_TREE.md
    │   ├── ProjectState.md
    │   ├── releases
    │   │   └── BASELINE_v1.0.3.md
    │   ├── schemas
    │   │   └── vaccine_profile_q10.md
    │   └── scientific_models
    │       └── vvm_q10_model.md
    ├── pipeline.log
    ├── poetry.lock
    ├── PR_DESCRIPTIONS.md
    ├── pr_summary.md
    ├── pyproject.toml
    ├── pytest.ini
    ├── README.md
    ├── requirements.txt
    ├── run_windows_friendly.ps1
    ├── scripts
    │   ├── __init__.py
    │   ├── check_no_core_entity_imports.py
    │   ├── create_backup.py
    │   ├── create_test_data.py
    │   ├── debug_ft2.py
    │   ├── generate_pdf_report.py
    │   ├── lock_infrastructure.sh
    │   ├── project_tree_guard.py
    │   ├── project_utility.py
    │   ├── run_ft2_pipeline.py
    │   ├── simple_pipeline.py
    │   ├── simulate_vvm_scenarios.py
    │   └── verify_visual_reports.py
    ├── src
    │   ├── __init__.py
    │   ├── api
    │   │   └── __init__.py
    │   ├── application
    │   │   ├── __init__.py
    │   │   ├── dtos
    │   │   │   ├── __init__.py
    │   │   │   ├── analysis_result_dto.py
    │   │   │   ├── base_dto.py
    │   │   │   ├── center_dto.py
    │   │   │   ├── evaluate_cold_chain_safety_request.py
    │   │   │   ├── report_input_dto.py
    │   │   │   └── vaccine_dto.py
    │   │   ├── mappers
    │   │   │   ├── __init__.py
    │   │   │   ├── center_mapper.py
    │   │   │   ├── exposure_mapper.py
    │   │   │   └── vaccine_mapper.py
    │   │   ├── ports
    │   │   │   ├── __init__.py
    │   │   │   ├── ft2_reader_port.py
    │   │   │   ├── i_reporter.py
    │   │   │   ├── i_repository.py
    │   │   │   ├── logger_port.py
    │   │   │   ├── report_generator_port.py
    │   │   │   └── validation_port.py
    │   │   └── use_cases
    │   │       ├── __init__.py
    │   │       ├── base_use_case.py
    │   │       ├── evaluate_cold_chain_safety_uc.py
    │   │       ├── evaluate_cold_chain_safety_use_case.py
    │   │       ├── generate_report_uc.py
    │   │       └── import_ft2_data_uc.py
    │   ├── domain
    │   │   ├── __init__.py
    │   │   ├── calculators
    │   │   │   ├── __init__.py
    │   │   │   ├── ccm_calculator.py
    │   │   │   ├── her_calculator.py
    │   │   │   └── vvm_q10_model.py
    │   │   ├── engines
    │   │   │   ├── __init__.py
    │   │   │   └── heat_exposure_engine.py
    │   │   ├── entities
    │   │   │   ├── __init__.py
    │   │   │   ├── ft2_entry.py
    │   │   │   ├── temperature_reading.py
    │   │   │   ├── vaccination_center.py
    │   │   │   └── vaccine.py
    │   │   ├── enums
    │   │   │   └── vvm_stage.py
    │   │   ├── exceptions
    │   │   │   └── __init__.py
    │   │   ├── models
    │   │   │   ├── __init__.py
    │   │   │   └── temperature_exposure.py
    │   │   ├── rules
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── rules_engine.py
    │   │   └── value_objects
    │   │       ├── __init__.py
    │   │       └── temperature_entry.py
    │   ├── infrastructure
    │   │   ├── __init__.py
    │   │   ├── adapters
    │   │   │   ├── __init__.py
    │   │   │   ├── ft2_reader
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── models
    │   │   │   │   │   └── __init__.py
    │   │   │   │   ├── parser
    │   │   │   │   │   ├── __init__.py
    │   │   │   │   │   └── ft2_parser.py
    │   │   │   │   ├── services
    │   │   │   │   │   ├── __init__.py
    │   │   │   │   │   └── ft2_linker.py
    │   │   │   │   └── validator
    │   │   │   │       ├── __init__.py
    │   │   │   │       └── ft2_validator.py
    │   │   │   ├── ft2_reader_adapter.py
    │   │   │   ├── ft2_repository_adapter.py
    │   │   │   └── noop_reporter_adapter.py
    │   │   ├── ingestion
    │   │   │   ├── __init__.py
    │   │   │   ├── ft2_converter.py
    │   │   │   ├── ft2_linker.py
    │   │   │   └── ft2_parser.py
    │   │   ├── logging.py
    │   │   ├── parsers
    │   │   │   └── __init__.py
    │   │   ├── validation
    │   │   │   ├── __init__.py
    │   │   │   └── default_validator.py
    │   │   └── validators
    │   │       └── __init__.py
    │   ├── intelligence
    │   │   └── __init__.py
    │   ├── main.py
    │   ├── presentation
    │   │   ├── __init__.py
    │   │   ├── cli
    │   │   │   ├── __init__.py
    │   │   │   └── cli.py
    │   │   ├── messages
    │   │   │   ├── __init__.py
    │   │   │   └── message_map.py
    │   │   └── reporting
    │   │       ├── __init__.py
    │   │       ├── arabic_pdf_generator.py
    │   │       ├── csv_reporter.py
    │   │       ├── guard.py
    │   │       ├── pdf_generator.py
    │   │       ├── professional_pdf_generator.py
    │   │       ├── simple_pdf_generator.py
    │   │       └── unified_pdf_generator.py
    │   ├── shared
    │   │   ├── __init__.py
    │   │   └── di_container.py
    │   └── utils
    │       ├── __init__.py
    │       ├── config_loader.py
    │       ├── vaccine_library_loader.py
    │       └── yaml_loader.py
    ├── tests
    │   ├── __init__.py
    │   ├── architecture
    │   │   ├── __init__.py
    │   │   └── test_domain_contracts.py
    │   ├── integration
    │   │   ├── __init__.py
    │   │   ├── test_cli.py
    │   │   ├── test_evaluate_cold_chain_uc.py
    │   │   ├── test_no_entity_leak.py
    │   │   ├── test_vaccine_library.py
    │   │   └── test_vvm_biological_scenarios.py
    │   ├── reporting
    │   │   ├── __init__.py
    │   │   ├── __snapshots__
    │   │   │   ├── __init__.py
    │   │   │   └── test_centers_report_snapshot.ambr
    │   │   └── snapshots
    │   │       ├── __init__.py
    │   │       └── test_centers_report_snapshot
    │   │           ├── __snapshots__
    │   │           │   └── test_centers_report_snapshot.ambr
    │   │           ├── test_centers_report_snapshot
    │   │           │   └── centers_report_snapshot.tsv
    │   │           └── test_centers_report_snapshot.py
    │   ├── test_phase2_structural_check.py
    │   └── unit
    │       ├── __init__.py
    │       ├── application
    │       │   ├── __init__.py
    │       │   └── use_cases
    │       │       ├── __init__.py
    │       │       └── test_evaluate_cold_chain_safety_use_case.py
    │       ├── test_ccm_calculator.py
    │       ├── test_debug_ft2.py
    │       ├── test_ft2_linker.py
    │       ├── test_ft2_parser.py
    │       ├── test_ft2_validator.py
    │       ├── test_generate_pdf_report.py
    │       ├── test_phase2_smoke.py
    │       ├── test_rules_logic.py
    │       ├── test_simulate_vvm_scenarios.py
    │       ├── test_vaccination_center.py
    │       ├── test_verify_visual_reports.py
    │       ├── test_vvm_q10_model.py
    │       └── test_vvm_stage.py
    └── tools
        └── legacy
            ├── simulate_vvm_scenarios.py
            └── tests
                ├── __init__.py
                ├── integration
                │   ├── __init__.py
                │   ├── test_evaluate_cold_chain_uc.py
                │   └── test_vaccine_library.py
                └── integrationmkdir
```
