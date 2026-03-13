#!/bin/bash
# Phase 3 Final Verification Script

echo "=========================================="
echo "🎯 Phase 3 Final Verification"
echo "=========================================="

# 1. تنظيف pycache
echo -e "\n📌 Step 0: Clean pycache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# 2. VaccinationCenter
echo -e "\n📌 VaccinationCenter..."
pytest tests/unit/test_vaccination_center.py -q
pytest tests/integration/test_vvm_biological_scenarios.py -q
pytest tests/unit/test_ft2_linker.py -q

# 3. UseCase
echo -e "\n📌 GenerateDeviceReportUseCase..."
pytest tests/unit/test_generate_device_report_uc.py -q
pytest tests/integration/test_generate_device_report_uc.py -q

# 4. CCMCalculator
echo -e "\n📌 CCMCalculator..."
pytest tests/unit/test_ccm_calculator.py -q

# 5. RetentionPolicy
echo -e "\n📌 RetentionPolicy..."
pytest tests/unit/domain/test_retention_policy.py -q

# 6. PDF Wrapper
echo -e "\n📌 PDF Wrapper..."
pytest tests/unit/test_unified_pdf_generator_wrapper.py -q
pytest tests/integration/test_pdf_fallback_chain.py -q

# 7. Quick Fixes
echo -e "\n📌 Quick Fixes..."
pytest tests/unit/test_chart_builder.py -q
pytest tests/unit/test_gui_ft2_behavior.py -q

# 8. Full Suite
echo -e "\n📌 Full Test Suite..."
pytest --tb=short -q

echo -e "\n=========================================="
echo "✅ Phase 3 Verification Complete"
echo "=========================================="
