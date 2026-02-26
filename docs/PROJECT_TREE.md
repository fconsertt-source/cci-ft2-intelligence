```tree
└── cci-ft2-intelligence
    ├── -H
    ├── .continue
    │   └── agents
    │       ├── new-config-1.yaml
    │       └── new-config.yaml
    ├── .github
    │   ├── architecture-guards.yml
    │   ├── CODEOWNERS
    │   └── workflows
    │       ├── architecture-guards.yml
    │       └── guard.yml
    ├── .gitignore
    ├── .pre-commit-config.yaml
    ├── .qodo
    │   ├── agents
    │   └── workflows
    ├── assets
    │   └── fonts
    ├── backup
    │   ├── backup_20260131_000840.tar.gz
    │   ├── backup_20260203_171607.tar.gz
    │   ├── backup_20260204_030429.tar.gz
    │   ├── backup_20260204_224545.tar.gz
    │   ├── backup_20260205_001514.tar.gz
    │   ├── backup_20260205_005209.tar.gz
    │   ├── backup_20260206_022628.tar.gz
    │   ├── backup_20260206_124646.tar.gz
    │   ├── backup_20260206_210230.tar.gz
    │   ├── backup_20260207_005231.tar.gz
    │   ├── backup_20260207_131444.tar.gz
    │   ├── backup_20260208_131557.tar.gz
    │   ├── backup_20260208_132109.tar.gz
    │   ├── backup_20260208_153918.tar.gz
    │   ├── backup_20260208_182911.tar.gz
    │   └── backup_20260208_235639.tar.gz
    ├── config
    │   ├── __init__.py
    │   ├── center_profiles.yaml
    │   ├── center_profiles_enhanced.yaml
    │   ├── ci_guard.yml
    │   ├── device_center_mapping.yaml
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
    │   │   ├── 130600112757_202305041136.txt
    │   │   ├── 130600113438_202407221216.txt
    │   │   ├── 130600205168_202503131237.txt
    │   │   └── __init__.py
    │   ├── input_raw
    │   │   ├── __init__.py
    │   │   ├── freeze_clinic_130600112767.csv
    │   │   ├── heat_mobile_130600112769.csv
    │   │   ├── safe_hospital_130600112764.csv
    │   │   └── test_data.csv
    │   ├── keys
    │   │   └── public.pem
    │   ├── output
    │   │   ├── __init__.py
    │   │   ├── detailed_reports
    │   │   │   ├── report_001.txt
    │   │   │   ├── report_002.txt
    │   │   │   ├── report_003.txt
    │   │   │   └── report_004.txt
    │   │   ├── reports
    │   │   │   ├── detailed_reports
    │   │   │   └── device_reports
    │   │   │       └── device_130600112764_report.json
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
    │   │   ├── 0009-presentation-boundary-lock.md
    │   │   └── ADR-0010: Safe Interface-Construction-on-a-Hardened-Referen.mdce
    │   ├── architecture
    │   │   ├── __init__.py
    │   │   ├── ARCHITECTURAL_RETROSPECTIVE_PHASE_4.md
    │   │   ├── DECISION_MATRIX.md
    │   │   ├── ENGINEERING_CHARTER.md
    │   │   └── ROADMAP_v2_POST_PHASE_4.md
    │   ├── Clean_Architecture_Project.md
    │   ├── decision_matrix.md
    │   ├── evolutionary_artifacts
    │   │   ├── berlinger_format_specs.md
    │   │   └── run_windows_friendly.ps1
    │   ├── foundational_charter.md
    │   ├── phase-a-hardened-architecture-plan.md
    │   ├── PHASE_5_SCOPE.md
    │   ├── project-retrospective.md
    │   ├── project_retrospective.md
    │   ├── project_state_manifest.json
    │   ├── PROJECT_TREE.md
    │   ├── ProjectState.md
    │   ├── releases
    │   │   ├── BASELINE_v1.0.3.md
    │   │   └── PHASE_4_COMPLETE.md
    │   ├── schemas
    │   │   └── vaccine_profile_q10.md
    │   └── scientific_models
    │       └── vvm_q10_model.md
    ├── ft2_data.json
    ├── pipeline.log
    ├── poetry.lock
    ├── PR_DESCRIPTIONS.md
    ├── pr_summary.md
    ├── pyproject.toml
    ├── pytest.ini
    ├── README.md
    ├── requirements.txt
    ├── run_phase3_verification.sh
    ├── scripts
    │   ├── __init__.py
    │   ├── check_di_container_usage.py
    │   ├── check_layer_dependencies.py
    │   ├── check_no_core_entity_imports.py
    │   ├── check_src_root_clean.py
    │   ├── create_backup.py
    │   ├── create_test_data.py
    │   ├── debug_ft2.py
    │   ├── generate_pdf_report.py
    │   ├── license-gen.py
    │   ├── lock_infrastructure.sh
    │   ├── project_tree_guard.py
    │   ├── project_utility.py
    │   ├── run_ft2_pipeline.py
    │   ├── simple_pipeline.py
    │   ├── simulate_vvm_scenarios.py
    │   └── verify_visual_reports.py
    ├── src
    │   ├── __init__.py
    │   ├── application
    │   │   ├── __init__.py
    │   │   ├── dtos
    │   │   │   ├── __init__.py
    │   │   │   ├── analysis_result_dto.py
    │   │   │   ├── base_dto.py
    │   │   │   ├── center_dto.py
    │   │   │   ├── device_report_dto.py
    │   │   │   ├── evaluate_cold_chain_safety_request.py
    │   │   │   ├── ft2_entry_dto.py
    │   │   │   ├── report_input_dto.py
    │   │   │   └── vaccine_dto.py
    │   │   ├── mappers
    │   │   │   ├── __init__.py
    │   │   │   ├── center_mapper.py
    │   │   │   ├── exposure_mapper.py
    │   │   │   └── vaccine_mapper.py
    │   │   ├── ports
    │   │   │   ├── __init__.py
    │   │   │   ├── device_repository_port.py
    │   │   │   ├── ft2_reader_port.py
    │   │   │   ├── ft2_writer_port.py
    │   │   │   ├── i_reporter.py
    │   │   │   ├── i_repository.py
    │   │   │   ├── logger_port.py
    │   │   │   ├── report_generator_port.py
    │   │   │   ├── thermal_degradation_estimator_port.py
    │   │   │   ├── thermal_impact_calculator_port.py
    │   │   │   ├── vaccine_repository_port.py
    │   │   │   ├── vaccine_specification_port.py
    │   │   │   ├── validation_port.py
    │   │   │   └── validation_protocol_port.py
    │   │   ├── security
    │   │   │   ├── __init__.py
    │   │   │   ├── license_guard.py
    │   │   │   └── license_validator.py
    │   │   ├── services
    │   │   │   ├── analysis_result_service.py
    │   │   │   └── device_center_mapper.py
    │   │   └── use_cases
    │   │       ├── __init__.py
    │   │       ├── base_use_case.py
    │   │       ├── evaluate_cold_chain_safety_uc.py
    │   │       ├── evaluate_cold_chain_safety_use_case.py
    │   │       ├── generate_device_report_uc.py
    │   │       ├── generate_report_uc.py
    │   │       ├── import_ft2_data_uc.py
    │   │       └── track_batch_exposure_uc.py
    │   ├── domain
    │   │   ├── __init__.py
    │   │   ├── calculators
    │   │   │   ├── __init__.py
    │   │   │   ├── ccm_calculator.py
    │   │   │   ├── her_calculator.py
    │   │   │   ├── q10_thermal_calculator.py
    │   │   │   └── vvm_q10_model.py
    │   │   ├── engines
    │   │   │   ├── __init__.py
    │   │   │   └── heat_exposure_engine.py
    │   │   ├── entities
    │   │   │   ├── __init__.py
    │   │   │   ├── cooling_device.py
    │   │   │   ├── ft2_entry.py
    │   │   │   ├── heat_exposure.py
    │   │   │   ├── temperature_reading.py
    │   │   │   ├── thermal_record.py
    │   │   │   ├── vaccination_center.py
    │   │   │   ├── vaccine.py
    │   │   │   └── vaccine_batch.py
    │   │   ├── enums
    │   │   │   ├── __init__.py
    │   │   │   ├── regulatory_status.py
    │   │   │   ├── safety_status.py
    │   │   │   └── vvm_stage.py
    │   │   ├── exceptions
    │   │   │   ├── __init__.py
    │   │   │   └── license_exceptions.py
    │   │   ├── models
    │   │   │   ├── __init__.py
    │   │   │   └── temperature_exposure.py
    │   │   ├── policies
    │   │   │   ├── __init__.py
    │   │   │   └── trial_policy.py
    │   │   ├── rules
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   ├── __init__.py
    │   │   │   ├── her_calculator_service.py
    │   │   │   ├── regulatory_decision_service.py
    │   │   │   ├── rules_engine.py
    │   │   │   └── thermal_degradation_estimator.py
    │   │   └── value_objects
    │   │       ├── __init__.py
    │   │       ├── temperature_entry.py
    │   │       └── vaccine_specification.py
    │   ├── infrastructure
    │   │   ├── __init__.py
    │   │   ├── adapters
    │   │   │   ├── __init__.py
    │   │   │   ├── berlinger_ft2_reader.py
    │   │   │   ├── default_ft2_reader.py
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
    │   │   │   ├── json_device_repository.py
    │   │   │   ├── json_ft2_data_writer.py
    │   │   │   ├── json_vaccine_repository.py
    │   │   │   ├── json_vaccine_spec_repository.py
    │   │   │   ├── noop_reporter_adapter.py
    │   │   │   ├── pdf_report_generator.py
    │   │   │   └── validation_protocol_service.py
    │   │   ├── ingestion
    │   │   │   ├── __init__.py
    │   │   │   ├── ft2_converter.py
    │   │   │   ├── ft2_linker.py
    │   │   │   └── ft2_parser.py
    │   │   ├── logging.py
    │   │   ├── parsers
    │   │   │   └── __init__.py
    │   │   ├── security
    │   │   │   ├── __init__.py
    │   │   │   ├── encrypted_license_repository.py
    │   │   │   ├── fingerprint_provider.py
    │   │   │   └── license_activator.py
    │   │   ├── utils
    │   │   │   ├── __init__.py
    │   │   │   ├── config_loader.py
    │   │   │   ├── vaccine_library_loader.py
    │   │   │   └── yaml_loader.py
    │   │   ├── validation
    │   │   │   ├── __init__.py
    │   │   │   └── default_validator.py
    │   │   └── validators
    │   │       └── __init__.py
    │   ├── presentation
    │   │   ├── __init__.py
    │   │   ├── cli
    │   │   │   ├── __init__.py
    │   │   │   ├── architectural_smoke_test.py
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
    │   └── shared
    │       ├── __init__.py
    │       └── di_container.py
    ├── tests
    │   ├── __init__.py
    │   ├── architecture
    │   │   ├── __init__.py
    │   │   ├── _guard_layer_separation_baseline.py
    │   │   ├── test_decision_path_separation.py
    │   │   ├── test_domain_contracts.py
    │   │   ├── test_domain_layer_sealed.py
    │   │   └── test_guard_layer_separation.py
    │   ├── bdd
    │   │   ├── test_excursion_device_scenario.py
    │   │   └── test_safe_device_scenario.py
    │   ├── conftest.py
    │   ├── integration
    │   │   ├── __init__.py
    │   │   ├── test_evaluate_cold_chain_uc.py
    │   │   ├── test_generate_device_report_uc.py
    │   │   ├── test_guard_stress.py
    │   │   ├── test_import_device_connection.py
    │   │   ├── test_license_gen.py
    │   │   ├── test_no_entity_leak.py
    │   │   ├── test_real_time_rollback.py
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
    │       ├── test_encrypted_license_repository.py
    │       ├── test_fingerprint_tolerance.py
    │       ├── test_ft2_linker.py
    │       ├── test_ft2_parser.py
    │       ├── test_ft2_validator.py
    │       ├── test_generate_device_report_uc.py
    │       ├── test_generate_pdf_report.py
    │       ├── test_import_ft2_data_uc.py
    │       ├── test_license_guard_integration.py
    │       ├── test_license_validator.py
    │       ├── test_phase2_smoke.py
    │       ├── test_regulatory_decision_service.py
    │       ├── test_rules_logic.py
    │       ├── test_simulate_vvm_scenarios.py
    │       ├── test_trial_policy.py
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
                │   ├── test_cli.py
                │   ├── test_evaluate_cold_chain_uc.py
                │   └── test_vaccine_library.py
                └── integrationmkdir
```
