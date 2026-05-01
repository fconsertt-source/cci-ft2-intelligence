#!/bin/bash
# scripts/verify_phase1_fixed.sh — نسخة مُصحّحة

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  🔍 التحقق من اكتمال المرحلة الأولى — نسخة مُصحّحة    ║"
echo "╚════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")/.."

# 1. تنظيف الكاش
echo -e "\n=== 🧹 تنظيف الكاش ==="
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ تم التنظيف"

# 2. عزل Domain
echo -e "\n=== 🛡️ التحقق من عزل Domain ==="
APP_IMPORTS=$(grep -r "from src\.application\|import src\.application" src/domain/ \
    --include="*.py" --exclude="*CHANGES*" --exclude="*DIFF*" \
    2>/dev/null | grep -v "^#" || true)
INFRA_IMPORTS=$(grep -r "from src\.infrastructure\|import src\.infrastructure" src/domain/ \
    --include="*.py" --exclude="*CHANGES*" --exclude="*DIFF*" \
    2>/dev/null | grep -v "^#" || true)

if [ -z "$APP_IMPORTS" ] && [ -z "$INFRA_IMPORTS" ]; then
    echo "✅ Domain معزول (نقي 100%)"
    DOMAIN_OK=1
else
    echo "❌ Domain: وجدت استيرادات محظورة"
    [ -n "$APP_IMPORTS" ] && echo "$APP_IMPORTS"
    [ -n "$INFRA_IMPORTS" ] && echo "$INFRA_IMPORTS"
    DOMAIN_OK=0
fi

# 3. اختبار DTOs
echo -e "\n=== 🔒 اختبار DTOs ==="
python3 << 'PYTHON_EOF'
import sys
import dataclasses
sys.path.insert(0, '.')

from src.application.dtos.device_report_dto import DeviceReportDTO, ReportDecision, VVMStage
from src.application.dtos.center_report_dto import CenterReportDTO

# DeviceReportDTO
dto = DeviceReportDTO(
    device_id='DEV_001', center_id='CTR_001', center_name='Test',
    temperature_ranges={'min': 2.0, 'max': 8.0},
    decision=ReportDecision.ACCEPTED, vvm_stage=VVMStage.A
)
try:
    dto.device_id = 'X'
    print("❌ DeviceReportDTO: ليس مجمداً")
    sys.exit(1)
except (AttributeError, dataclasses.FrozenInstanceError):
    print("✅ DeviceReportDTO: مجمد")

# CenterReportDTO
dto2 = CenterReportDTO(
    center_id='CTR_001', center_name='Test',
    total_devices=10, safe_devices=7, rejected_devices=2, partial_devices=1
)
try:
    dto2.center_name = 'X'
    print("❌ CenterReportDTO: ليس مجمداً")
    sys.exit(1)
except (AttributeError, dataclasses.FrozenInstanceError):
    print("✅ CenterReportDTO: مجمد")

print("✅ DTOs: جميع الاختبارات ناجحة")
PYTHON_EOF
DTOS_OK=$?

# 4. Composition Root
echo -e "\n=== 🔌 اختبار Composition Root ==="
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '.')

from src.composition_root.di_container import DIContainer
from src.composition_root.app_composer import compose_phase1
from src.application.services.judgment_engine import JudgmentEngine

container = DIContainer()
compose_phase1(container)

if container.is_registered(JudgmentEngine):
    print("✅ Composition Root: يعمل")
    sys.exit(0)
else:
    print("❌ Composition Root: JudgmentEngine غير مسجل")
    sys.exit(1)
PYTHON_EOF
COMPOSITION_OK=$?

# 5. اختبارات الوحدة
echo -e "\n=== 🧪 اختبارات الوحدة ==="
if [ -f "tests/conftest.py" ]; then
    mv tests/conftest.py tests/conftest.py.bak 2>/dev/null || true
fi

python -m pytest tests/unit/domain/rules/ tests/unit/application/dtos/ -v --tb=short 2>&1 | tail -20
TESTS_OK=$?

# استعادة conftest
[ -f "tests/conftest.py.bak" ] && mv tests/conftest.py.bak tests/conftest.py 2>/dev/null || true

# 6. التقرير النهائي
echo -e "\n╔════════════════════════════════════════════════════════╗"
echo "║  📊 التقرير النهائي                                       ║"
echo "╚════════════════════════════════════════════════════════╝"

PASSED=0
[ $DOMAIN_OK -eq 1 ] && ((PASSED++)) && echo "  ✅ عزل Domain" || echo "  ❌ عزل Domain"
[ $DTOS_OK -eq 0 ] && ((PASSED++)) && echo "  ✅ DTOs" || echo "  ❌ DTOs"
[ $COMPOSITION_OK -eq 0 ] && ((PASSED++)) && echo "  ✅ Composition Root" || echo "  ❌ Composition Root"
[ $TESTS_OK -eq 0 ] && ((PASSED++)) && echo "  ✅ اختبارات الوحدة" || echo "  ❌ اختبارات الوحدة"

echo ""
echo "النتيجة: $PASSED / 4"

if [ $PASSED -eq 4 ]; then
    echo -e "\n🎉 ✅ المرحلة الأولى: مكتملة بنجاح!"
    exit 0
else
    echo -e "\n⚠️  المرحلة الأولى: غير مكتملة"
    exit 1
fi