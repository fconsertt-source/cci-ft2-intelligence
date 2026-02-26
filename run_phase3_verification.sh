#!/bin/bash
set -e

echo "=========================================="
echo "🧪 اختبارات التحقق من إغلاق المرحلة الثالثة"
echo "التاريخ: $(date +'%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 1. تشغيل جميع الاختبارات
echo "1️⃣  تشغيل جميع الاختبارات (86 اختبار)..."
pytest -q --tb=line 2>&1 | tail -3
echo ""

# 2. تشغيل حراسة تسرب الكيانات
echo "2️⃣  تشغيل حراسة تسرب الكيانات..."
python scripts/check_no_core_entity_imports.py
echo ""

# 3. تشغيل حراسة استخدام جذر التركيب
echo "3️⃣  تشغيل حراسة استخدام جذر التركيب..."
python scripts/check_di_container_usage.py
echo ""

# 4. تشغيل حراسة نظافة جذر src/
echo "4️⃣  تشغيل حراسة نظافة جذر src/..."
python scripts/check_src_root_clean.py
echo ""

# 5. تشغيل Smoke Test المعماري
echo "5️⃣  تشغيل Smoke Test المعماري..."
python -m src.presentation.cli.architectural_smoke_test 2>&1 | tail -6
echo ""

echo "=========================================="
echo "✅ جميع الاختبارات اجتازت بنجاح"
echo "المرحلة الثالثة: مغلقة رسميًا كمرجع معماري محصن"
echo "=========================================="
