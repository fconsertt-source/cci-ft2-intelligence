#!/usr/bin/env python3
"""
فحص المسافات الزائدة في ملفات JSON
يمنع أخطاء مثل: "app.title " بدلاً من "app.title"
"""

import json
import sys
from pathlib import Path


def check_json_file(filepath: Path) -> bool:
    """التحقق من ملف JSON واحد"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)

        errors = []

        # فحص المفاتيح
        for key in data.keys():
            if key != key.strip():
                errors.append(f"مفتاح به مسافات زائدة: '{key}' → '{key.strip()}'")

        # فحص القيم النصية
        for key, value in data.items():
            if isinstance(value, str) and value != value.strip():
                errors.append(f"قيمة به مسافات زائدة في '{key}': '{value[:50]}...'")

        if errors:
            print(f"\n❌ {filepath}:")
            for error in errors:
                print(f"   {error}")
            return False

        print(f"✅ {filepath}: نظيف")
        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ {filepath}: JSON غير صالح - {e}")
        return False
    except Exception as e:
        print(f"\n❌ {filepath}: خطأ غير متوقع - {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python check_json_spaces.py <file1.json> [file2.json ...]")
        sys.exit(1)

    all_clean = True
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if path.exists():
            if not check_json_file(path):
                all_clean = False
        else:
            print(f"⚠️  {filepath}: ملف غير موجود")

    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
