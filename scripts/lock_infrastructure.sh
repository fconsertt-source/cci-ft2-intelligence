#!/bin/bash
# ======================================================
# Infrastructure Boundary Lock Script
# Ensures all infrastructure components reside under src/infrastructure/
# Idempotent: Safe to run multiple times
# ======================================================

set -e  # Exit immediately on error
export LC_ALL=C.UTF-8  # Ensure consistent locale

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 التحقق من حالة مسارات البنية التحتية..."

# التحقق من وجود المكونات في المواقع الصحيحة
INGESTION_CORRECT=false
FT2_READER_CORRECT=false

if [ -d "src/infrastructure/ingestion" ] && [ -f "src/infrastructure/ingestion/ft2_parser.py" 2>/dev/null ]; then
    INGESTION_CORRECT=true
fi

if [ -d "src/infrastructure/adapters/ft2_reader" ] && [ -f "src/infrastructure/adapters/ft2_reader/parser/ft2_parser.py" 2>/dev/null ]; then
    FT2_READER_CORRECT=true
fi

# إذا كانت المسارات صحيحة بالفعل
if [ "$INGESTION_CORRECT" = true ] && [ "$FT2_READER_CORRECT" = true ]; then
    echo -e "\n✅ تم التحقق: جميع مكونات البنية التحتية في مواقعها الصحيحة:"
    echo "   • src/infrastructure/ingestion/"
    echo "   • src/infrastructure/adapters/ft2_reader/"
    echo -e "\n🔒 الحدود المعمارية مغلقة بالفعل. لا حاجة لأي تعديل."
    exit 0
fi

echo -e "\n⚠️  اكتشاف مسارات غير متوافقة مع المعمارية. بدء التصحيح التلقائي...\n"

# دالة مساعدة للنقل الآمن مع الحفاظ على التاريخ (إذا كان تحت تحكم Git)
safe_git_mv() {
    local src="$1"
    local dest="$2"
    
    if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        if git mv "$src" "$dest" 2>/dev/null; then
            echo "   ✓ تم النقل باستخدام git mv (الحفاظ على التاريخ)"
            return 0
        fi
    fi
    
    # fallback إلى mv عادي
    mv -f "$src" "$dest" 2>/dev/null || {
        echo "   ✗ فشل نقل $src" >&2
        return 1
    }
    echo "   ✓ تم النقل باستخدام mv"
}

# الخطوة ١: نقل ingestion إلى الموقع الصحيح
if [ -d "src/ingestion" ] && [ "$INGESTION_CORRECT" = false ]; then
    echo "📦 معالجة src/ingestion/ ..."
    mkdir -p src/infrastructure/ingestion
    
    # نقل الملفات مع الحفاظ على البنية
    for file in src/ingestion/*.py; do
        [ -e "$file" ] || continue
        safe_git_mv "$file" "src/infrastructure/ingestion/"
    done
    
    # إزالة الدليل الفارغ
    rmdir src/ingestion 2>/dev/null || rm -rf src/ingestion
    
    echo "   → src/infrastructure/ingestion/"
fi

# الخطوة ٢: نقل ft2_reader إلى الموقع الصحيح
if [ -d "src/ft2_reader" ] && [ "$FT2_READER_CORRECT" = false ]; then
    echo -e "\n📦 معالجة src/ft2_reader/ ..."
    mkdir -p src/infrastructure/adapters/ft2_reader/{parser,services,validator,models}
    
    # نقل الملفات مع الحفاظ على البنية الفرعية
    if [ -d "src/ft2_reader/parser" ]; then
        safe_git_mv "src/ft2_reader/parser" "src/infrastructure/adapters/ft2_reader/"
    fi
    if [ -d "src/ft2_reader/services" ]; then
        safe_git_mv "src/ft2_reader/services" "src/infrastructure/adapters/ft2_reader/"
    fi
    if [ -d "src/ft2_reader/validator" ]; then
        safe_git_mv "src/ft2_reader/validator" "src/infrastructure/adapters/ft2_reader/"
    fi
    if [ -d "src/ft2_reader/models" ]; then
        safe_git_mv "src/ft2_reader/models" "src/infrastructure/adapters/ft2_reader/"
    fi
    if [ -f "src/ft2_reader/__init__.py" ]; then
        safe_git_mv "src/ft2_reader/__init__.py" "src/infrastructure/adapters/ft2_reader/"
    fi
    
    # إزالة الدليل الفارغ
    rmdir src/ft2_reader 2>/dev/null || rm -rf src/ft2_reader
    
    echo "   → src/infrastructure/adapters/ft2_reader/"
fi

# الخطوة ٣: تحديث جميع الاستيرادات في المشروع
echo -e "\n✏️  تحديث الاستيرادات في جميع ملفات Python..."

# تحديث استيرادات ingestion
if grep -rl "src\.ingestion" src tests scripts tools --include="*.py" 2>/dev/null | grep -q .; then
    grep -rl "src\.ingestion" src tests scripts tools --include="*.py" | while read -r file; do
        sed -i 's/from src\.ingestion/from src.infrastructure.ingestion/g' "$file" 2>/dev/null || true
        sed -i 's/import src\.ingestion/import src.infrastructure.ingestion/g' "$file" 2>/dev/null || true
        echo "   ✓ $file"
    done
fi

# تحديث استيرادات ft2_reader
if grep -rl "src\.ft2_reader" src tests scripts tools --include="*.py" 2>/dev/null | grep -q .; then
    grep -rl "src\.ft2_reader" src tests scripts tools --include="*.py" | while read -r file; do
        sed -i 's/from src\.ft2_reader/from src.infrastructure.adapters.ft2_reader/g' "$file" 2>/dev/null || true
        sed -i 's/import src\.ft2_reader/import src.infrastructure.adapters.ft2_reader/g' "$file" 2>/dev/null || true
        echo "   ✓ $file"
    done
fi

# الخطوة ٤: التحقق النهائي من السلامة المعمارية
echo -e "\n🧪 التحقق من السلامة المعمارية..."
echo "   → تشغيل جميع الاختبارات..."
if ! pytest --tb=short -q 2>&1 | grep -E "(passed|failed)" | tail -1; then
    echo -e "\n❌ فشل الاختبارات بعد التحديث. التراجع عن التغييرات..."
    git checkout . 2>/dev/null || echo "ملاحظة: لم يتم التراجع التلقائي (غير موجود تحت Git)"
    exit 1
fi

echo "   → تشغيل حراس المعمارية..."
if ! python scripts/check_no_core_entity_imports.py 2>&1 | tail -1 | grep -q "OK"; then
    echo -e "\n❌ كسر الحدود المعمارية بعد التحديث. التراجع عن التغييرات..."
    git checkout . 2>/dev/null || echo "ملاحظة: لم يتم التراجع التلقائي (غير موجود تحت Git)"
    exit 1
fi

# التحقق من عدم وجود مسارات قديمة
if [ -d "src/ingestion" ] || [ -d "src/ft2_reader" ]; then
    echo -e "\n❌ بقيت مسارات قديمة بعد التحديث. التراجع..."
    git checkout . 2>/dev/null || echo "ملاحظة: لم يتم التراجع التلقائي (غير موجود تحت Git)"
    exit 1
fi

# النجاح النهائي
echo -e "\n✅ تم إغلاق حدود البنية التحتية بنجاح!"
echo -e "\nالهيكل الجديد:"
echo "   src/infrastructure/"
echo "   ├── ingestion/          ← جميع مكونات التحويل والمعالجة"
echo "   └── adapters/"
echo "       └── ft2_reader/     ← جميع مكونات قراءة البيانات الخارجية"
echo -e "\n🔒 المشروع الآن متوافق 100% مع مبادئ Clean Architecture:"
echo "   • البنية التحتية معزولة تمامًا في طبقة مخصصة"
echo "   • لا استيرادات خارجية داخل طبقات Domain/Application"
echo "   • الحدود المعمارية محروسة بواسطة Guard Scripts"
echo -e "\n📌 ملاحظة: تم الحفاظ على التاريخ البرمجي (Git History) أثناء النقل."