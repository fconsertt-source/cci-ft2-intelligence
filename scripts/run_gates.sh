#!/bin/bash
# Run all pre-launch gates sequentially

echo "Running Gate A: Code Stability"
pytest tests/unit/ tests/integration/ -q --tb=short || exit 1
python scripts/check_no_core_entity_imports.py && \
python scripts/check_di_container_usage.py && \
python scripts/check_src_root_clean.py && \
python scripts/check_layer_dependencies.py || exit 1
python -m scripts.audit_ledger | grep -E "VERIFIED" || exit 1


echo "Running Gate B: End-to-End Scenario"
python -m scripts.process_ft2 data/input_ft2/incoming/ || exit 1
python -m scripts.verify_visual_reports || exit 1
python -m scripts.audit_ledger | grep -E "VERIFIED" || exit 1
python -m src.presentation.cli.gui_main --help || echo "GUI check skipped (requires display)"


echo "Running Gate C: Visual Outputs"
ls -lh data/output/visual_tests/*.pdf data/output/visual_tests/*.png || exit 1
file data/output/visual_tests/temp_dist.png || exit 1

echo "All gates passed."
