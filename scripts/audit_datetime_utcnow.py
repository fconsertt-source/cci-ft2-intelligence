#!/usr/bin/env python3
"""
🔍 أداة تحليل استخدامات utc_now_iso() - المرحلة الأولى (قراءة فقط)
ترصد جميع استخدامات الدالة المهملة وتصنفها مع اقتراحات الإصلاح.

الاستخدام:
    python scripts/audit_datetime_utcnow.py
    python scripts/audit_datetime_utcnow.py --output report.txt
    python scripts/audit_datetime_utcnow.py --verbose
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ==============================================
# الإعدادات والتكوين
# ==============================================
PROJECT_DIRS = ["src", "tests", "scripts"]
EXCLUDE_DIRS = ["__pycache__", ".git", "venv", "env", ".pytest_cache", "dist", "build"]
FILE_PATTERNS = ["*.py"]

# الأنماط النصية للبحث
UTC_PATTERN = re.compile(r"datetime\.utcnow\(\)")
TIMESPEC_PATTERN = re.compile(r'isoformat\(\s*timespec\s*=\s*["\'](\w+)["\']\s*\)')
ASSERT_PATTERN = re.compile(r"assert\s+.*==.*")
IMPORT_PATTERN = re.compile(r"^(from|import)\s+datetime")

# ==============================================
# دوال مساعدة
# ==============================================


def should_exclude(path: Path) -> bool:
    """تحديد ما إذا كان يجب استبعاد المجلد"""
    return any(excluded in str(path) for excluded in EXCLUDE_DIRS)


def detect_context(
    path: Path, line: str, next_line: Optional[str] = None
) -> Tuple[str, str]:
    """
    تحديد سياق الاستخدام (إنتاج/اختبار) ونوع المقارنة إن وجد.
    """
    path_str = str(path).lower()

    # تحديد السياق
    if "tests/" in path_str or path_str.startswith("tests/") or "test_" in path.name:
        context = "🧪 اختبار"
    else:
        context = "⚙️ إنتاج"

    # تحديد نوع المقارنة
    compare_type = "-"
    if ASSERT_PATTERN.search(line):
        compare_type = "🔴 مقارنة حرفية"
    elif next_line and ASSERT_PATTERN.search(next_line):
        compare_type = "🔴 مقارنة حرفية (سطر تالٍ)"

    return context, compare_type


def suggest_fix(line: str, timespec: Optional[str] = None) -> str:
    """
    اقتراح الإصلاح المناسب للسطر.
    """
    # استخراج المسافة البادئة

    # بناء الدالة المقترحة
    if timespec:
        replacement = f'utc_now_iso(timespec="{timespec}")'
    else:
        replacement = "utc_now_iso()"

    new_line = re.sub(r"datetime\.utcnow\(\)", replacement, line)

    return new_line


def check_import_exists(file_path: Path) -> bool:
    """التحقق من وجود استيراد datetime في الملف"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return bool(IMPORT_PATTERN.search(content))
    except Exception:
        return False


def format_report(results: List[Dict], stats: Dict) -> str:
    """تنسيق التقرير النهائي"""
    lines = []
    lines.append("=" * 80)
    lines.append(
        f"📋 تقرير تحليل استخدامات utc_now_iso() - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    lines.append("=" * 80)
    lines.append("")

    if not results:
        lines.append("✅ لم يتم العثور على أي استخدام لـ utc_now_iso()!")
        lines.append("")
        return "\n".join(lines)

    # تجميع النتائج حسب الملف
    by_file = defaultdict(list)
    for r in results:
        by_file[r["file"]].append(r)

    # عرض النتائج حسب الملف
    for file_path, file_results in sorted(by_file.items()):
        lines.append(f"📄 {file_path}")
        lines.append("-" * 80)

        for r in file_results:
            # عرض السطر مع الترقيم
            line_num = r["line"]
            code = r["code"]
            compare = r["compare_type"]
            suggested = r["suggested"]

            lines.append(f"  {line_num:4d} │ {code}")
            if compare != "-":
                lines.append(f"       ⚠️  {compare}")
            lines.append(f"       💡 → {suggested}")
            lines.append("")

        # معلومات إضافية عن الملف
        has_import = r.get("has_datetime_import", False)
        if not has_import:
            lines.append("       ℹ️  الملف لا يستورد datetime - سيحتاج إلى استيراد")
        lines.append("")

    # الملخص الإحصائي
    lines.append("=" * 80)
    lines.append("📊 الملخص الإحصائي")
    lines.append("-" * 80)
    lines.append(f"إجمالي الاستخدامات: {stats['total']}")
    lines.append(f"  • في ملفات الإنتاج: {stats['production']}")
    lines.append(f"  • في ملفات الاختبار: {stats['test']}")
    lines.append(f"  • مع مقارنات حرفية: {stats['literal_comparisons']}")
    lines.append(f"  • مع معامل timespec: {stats['with_timespec']}")
    lines.append("")
    lines.append(f"الملفات المتأثرة: {stats['files_affected']}")
    lines.append("")

    # توصيات
    lines.append("💡 التوصيات")
    lines.append("-" * 80)
    lines.append("1. أنشئ دالة مساعدة في src/utils/time.py:")
    lines.append("   ```python")
    lines.append("   from datetime import datetime, timezone")
    lines.append("   ")
    lines.append("   def utc_now_iso(timespec: str = 'seconds') -> str:")
    lines.append('       """إرجاع الوقت الحالي بصيغة ISO مع Zulu indicator"""')
    lines.append(
        "       return datetime.now(timezone.utc).isoformat(timespec=timespec).replace('+00:00', 'Z')"
    )
    lines.append("   ```")
    lines.append("")
    lines.append("2. للاختبارات ذات المقارنات الحرفية، استخدم:")
    lines.append("   ```python")
    lines.append("   from freezegun import freeze_time")
    lines.append("   ")
    lines.append("   @freeze_time('2025-01-01 12:00:00')")
    lines.append("   def test_with_fixed_time():")
    lines.append("       ...")
    lines.append("   ```")
    lines.append("")
    lines.append("3. أو تجاهل المنطقة الزمنية في المقارنة:")
    lines.append("   ```python")
    lines.append("   assert result.split('+')[0] == expected.split('+')[0]")
    lines.append("   ```")
    lines.append("")
    lines.append("=" * 80)
    lines.append("🔧 للتطبيق الفعلي، استخدم الخيار --apply في المرحلة الثانية")
    lines.append("=" * 80)

    return "\n".join(lines)


# ==============================================
# الدالة الرئيسية
# ==============================================


def main():
    parser = argparse.ArgumentParser(
        description="تحليل استخدامات utc_now_iso() - المرحلة الأولى"
    )
    parser.add_argument("--output", "-o", type=str, help="حفظ التقرير في ملف")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="عرض تفاصيل إضافية"
    )
    args = parser.parse_args()

    print("🔍 المرحلة الأولى: تحليل استخدامات utc_now_iso()")
    print("=" * 60)

    results = []
    stats = {
        "total": 0,
        "production": 0,
        "test": 0,
        "literal_comparisons": 0,
        "with_timespec": 0,
        "files_affected": 0,
    }

    affected_files = set()

    # البحث في المجلدات المحددة
    for project_dir in PROJECT_DIRS:
        if not os.path.exists(project_dir):
            if args.verbose:
                print(f"⚠️  المجلد غير موجود: {project_dir}")
            continue

        for root, dirs, files in os.walk(project_dir):
            # استبعاد المجلدات غير المرغوب فيها
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]

            for file in files:
                if not file.endswith(".py"):
                    continue

                file_path = Path(root) / file

                if should_exclude(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception as e:
                    if args.verbose:
                        print(f"❌ خطأ في قراءة {file_path}: {e}")
                    continue

                file_has_match = False

                for i, line in enumerate(lines):
                    if UTC_PATTERN.search(line):
                        file_has_match = True
                        stats["total"] += 1

                        # استخراج timespec إن وجد
                        timespec_match = TIMESPEC_PATTERN.search(line)
                        timespec = timespec_match.group(1) if timespec_match else None
                        if timespec:
                            stats["with_timespec"] += 1

                        # تحديد السياق ونوع المقارنة
                        next_line = lines[i + 1] if i + 1 < len(lines) else None
                        context, compare_type = detect_context(
                            file_path, line, next_line
                        )

                        if compare_type != "-":
                            stats["literal_comparisons"] += 1
                        if "اختبار" in context:
                            stats["test"] += 1
                        else:
                            stats["production"] += 1

                        # اقتراح الإصلاح
                        suggested = suggest_fix(line, timespec)

                        # التحقق من وجود استيراد datetime
                        has_import = check_import_exists(file_path)

                        results.append(
                            {
                                "file": str(file_path),
                                "line": i + 1,
                                "code": line.strip(),
                                "context": context,
                                "compare_type": compare_type,
                                "timespec": timespec,
                                "suggested": suggested,
                                "has_datetime_import": has_import,
                            }
                        )

                        if args.verbose:
                            print(f"  ✓ {file_path}:{i+1}")

                if file_has_match:
                    affected_files.add(str(file_path))

    stats["files_affected"] = len(affected_files)

    # إنشاء التقرير
    report = format_report(results, stats)

    # عرض التقرير
    print(report)

    # حفظ في ملف إذا طُلب
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ تم حفظ التقرير في: {args.output}")
        except Exception as e:
            print(f"❌ خطأ في حفظ التقرير: {e}")

    # ملاحظات ختامية
    if stats["total"] > 0:
        print("\n⚠️  هذه هي المرحلة الأولى فقط (تحليل).")
        print(
            "   للمرحلة الثانية (التطبيق)، استخدم: python scripts/fix_datetime.py --apply"
        )
        print("   بعد مراجعة النتائج والموافقة عليها.")

    return 0 if stats["total"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
