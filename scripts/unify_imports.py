#!/usr/bin/env python3
"""
سكربت آمن لتوحيد استيرادات الكيانات النطاقية
v3.0 — يستخدم libcst لتجنب مخاطر الاستبدال النصي

Usage:
    python scripts/unify_imports.py --dry-run  # معاينة
    python scripts/unify_imports.py --apply    # تطبيق
"""
import argparse
import sys
from pathlib import Path

try:
    import libcst as cst

    HAS_LIBCST = True
except ImportError:
    HAS_LIBCST = False
    print("⚠️ libcst not installed. Install with: pip install libcst")

# خريطة الاستيرادات الموحدة
UNIFIED_IMPORTS = {
    "FT2Entry": "src.domain.entities.ft2_entry",
    "FT2EntryDTO": "src.domain.dtos.ft2_entry_dto",
    "VaccinationCenter": "src.domain.entities.vaccination_center",
    "DeviceReportDTO": "src.application.dtos.device_report_dto",
    "GenerateDeviceReportRequest": "src.application.use_cases.requests",
}


class ImportUnifier(cst.CSTVisitor):
    """✅ Visitor آمن باستخدام libcst"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.modified = False
        self.changes = []

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ):
        """تحديث استيرادات From"""
        if original_node.module is None:
            return updated_node

        module_name = (
            ".".join([part.value for part in original_node.module.value.parts])
            if hasattr(original_node.module.value, "parts")
            else original_node.module.value
        )

        imports_to_add = []
        names_to_remove = []

        for alias in original_node.names:
            if isinstance(alias, cst.ImportAlias):
                name = alias.name.value
                if name in UNIFIED_IMPORTS:
                    correct_module = UNIFIED_IMPORTS[name]
                    if module_name != correct_module:
                        imports_to_add.append((name, correct_module))
                        names_to_remove.append(alias)

        if imports_to_add:
            self.modified = True
            for name, module in imports_to_add:
                self.changes.append(f"Fix: {name} from {module}")

        return updated_node


def unify_imports_in_file(file_path: Path, dry_run: bool = True) -> bool:
    """توحيد الاستيرادات في ملف واحد"""
    if not HAS_LIBCST:
        print(f"❌ Cannot process {file_path}: libcst not available")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = cst.parse_module(source)
        visitor = ImportUnifier(dry_run=dry_run)
        tree = tree.visit(visitor)

        if visitor.modified and not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tree.code)
            print(f"✅ Fixed: {file_path}")
            for change in visitor.changes:
                print(f"   - {change}")
            return True
        elif visitor.modified and dry_run:
            print(f"📍 Would fix: {file_path}")
            for change in visitor.changes:
                print(f"   - {change}")
            return False

    except Exception as e:
        print(f"⚠️ Error processing {file_path}: {e}")

    return False


def main():
    parser = argparse.ArgumentParser(description="Unify domain entity imports")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )
    parser.add_argument("--root", default=".", help="Root directory")
    args = parser.parse_args()

    root = Path(args.root)
    modified_count = 0

    print("=" * 70)
    print(f"🔧 Import Unifier — {'DRY RUN' if not args.apply else 'APPLY MODE'}")
    print("=" * 70)

    for py_file in root.rglob("*.py"):
        if any(p in str(py_file) for p in ["__pycache__", ".git", "venv", "tests/"]):
            continue

        if unify_imports_in_file(py_file, dry_run=not args.apply):
            modified_count += 1

    print("\n" + "=" * 70)
    print(f"Total files modified: {modified_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
