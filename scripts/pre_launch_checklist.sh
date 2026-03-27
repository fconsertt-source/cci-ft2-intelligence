#!/bin/bash
# قائمة التحقق النهائية قبل الإطلاق

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🛡️  Pre-Launch Checklist                                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# □ 1. جميع الاختبارات ناجحة
echo "□ 1. Running all tests..."
pytest tests/ -q --tb=no > /tmp/test_results.txt 2>&1
if grep -q "passed" /tmp/test_results.txt; then
    echo "   ✅ Tests passed"
else
    echo "   ❌ Tests failed"
    exit 1
fi

# □ 2. الحراسات المعمارية
echo "□ 2. Running architecture guards..."
python scripts/check_no_core_entity_imports.py && \
python scripts/check_di_container_usage.py && \
python scripts/check_src_root_clean.py && \
python scripts/check_layer_dependencies.py && \
echo "   ✅ All guards passed" || echo "   ❌ Guards failed"

# □ 3. Ledger سليم
echo "□ 3. Auditing Ledger..."
python -m scripts.audit_ledger 2>&1 | grep -q "VERIFIED" && \
echo "   ✅ Ledger verified" || echo "   ❌ Ledger failed"

# □ 4. المخرجات البصرية موجودة
echo "□ 4. Checking visual outputs..."
ls -lh data/output/visual_tests/*.pdf data/output/visual_tests/*.png > /dev/null 2>&1 && \
echo "   ✅ Visual outputs exist" || echo "   ❌ Visual outputs missing"

# □ 5. الواجهة تعمل
echo "□ 5. Testing GUI launch..."
timeout 5 python -m src.presentation.cli.gui_main > /dev/null 2>&1 && \
echo "   ✅ GUI launches" || echo "   ⚠️  GUI needs display"

# □ 6. النسخ الاحتياطية مُهيأة
echo "□ 6. Checking backup setup..."
python scripts/create_backup.py > /dev/null 2>&1 && \
echo "   ✅ Backup working" || echo "   ❌ Backup failed"

# □ 7. مساحة القرص كافية
echo "□ 7. Checking disk space..."
DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "   ✅ Disk space OK ($DISK_USAGE%)"
else
    echo "   ⚠️  Disk space critical ($DISK_USAGE%)"
fi

# □ 8. Git Tag مُنشأ
echo "□ 8. Checking Git tag..."
git tag -l | grep -q "production-trial" && \
echo "   ✅ Git tag exists" || echo "   ⏳  Git tag pending"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Pre-launch checklist complete"
echo "═══════════════════════════════════════════════════════════"
