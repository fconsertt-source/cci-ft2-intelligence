#!/usr/bin/env python3
"""
تحديث استيرادات DTO بعد النقل إلى domain
آمن عبر Linux/macOS/Windows
"""
import pathlib
import re

REPLACEMENTS = {
    # simple string replacements; regex not needed
    r"from src.application.dtos": "from src.domain.dtos",
    r"src.application.dtos": "src.domain.dtos",
}


def update_file(file_path: pathlib.Path) -> bool:
    """تحديث ملف واحد، إرجاع True إذا تم تغيير"""
    try:
        text = file_path.read_text(encoding="utf-8")
        new_text = text

        for old_pattern, new_val in REPLACEMENTS.items():
            new_text = re.sub(old_pattern, new_val, new_text)

        if new_text != text:
            file_path.write_text(new_text, encoding="utf-8")
            print(f"✅ Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error updating {file_path}: {e}")
        return False


def main():
    updated_count = 0

    # البحث في src/ و tests/
    for root_dir in ["src", "tests"]:
        for py_file in pathlib.Path(root_dir).rglob("*.py"):
            if update_file(py_file):
                updated_count += 1

    print(f"\n{'='*50}")
    print(f"✅ Completed: {updated_count} files updated")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
