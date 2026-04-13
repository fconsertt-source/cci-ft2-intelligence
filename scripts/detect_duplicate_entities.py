#!/usr/bin/env python3
"""
سكربت متقدم لكشف الكيانات المكررة أو المتشابهة في المشروع
Production-Grade v3.0 — مع معالجة False Positives و AST Normalization

Usage:
    python scripts/detect_duplicate_entities.py
"""
import ast
import hashlib
import io
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# ألوان للطباعة
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# ============================================================================
# ✅ تحسين 1: Whitelist للتكرارات الشرعية
# ============================================================================
ALLOWED_DUPLICATE_CLASSES = {
    "Config",
    "Settings",
    "Result",
    "Response",
    "Request",
    "DTO",
    "TestBase",
    "MockEntry",
    "_DummyFlowable",  # generated placeholder class used in builders
}

# المسارات التي يتم تجاهلها تماماً
IGNORED_PATHS = {
    "tests/",
    "test_",
    "__pycache__",
    ".git/",
    "venv/",
    ".pytest_cache/",
    "generated/",
    "migrations/",
}

# الكيانات الحرجة التي يجب أن تكون فريدة (Source of Truth)
CRITICAL_DOMAIN_ENTITIES = {
    "FT2Entry",
    "VaccinationCenter",
    "CCMCalculator",
}

CRITICAL_APPLICATION_DTOS = {
    "FT2EntryDTO",
    "DeviceReportDTO",
    "GenerateDeviceReportRequest",
    "RetentionPolicy",
}


@dataclass
class ImportInfo:
    """معلومات استيراد دقيقة"""

    file: Path
    module: str
    name: str
    alias: Optional[str]


class DuplicateDetector:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.class_definitions: Dict[str, List[Path]] = defaultdict(list)
        self.file_hashes: Dict[str, List[Path]] = defaultdict(list)
        self.import_map: Dict[str, List[ImportInfo]] = defaultdict(list)
        self.scanned_files_count: int = 0

    def _should_ignore_file(self, file_path: Path) -> bool:
        """✅ تحسين: تجاهل المسارات غير الحرجة"""
        path_str = str(file_path)
        return any(ignored in path_str for ignored in IGNORED_PATHS)

    def scan_all_python_files(self) -> List[Path]:
        """جمع جميع ملفات Python في المشروع"""
        files = []
        for py_file in self.root_dir.rglob("*.py"):
            if self._should_ignore_file(py_file):
                continue
            files.append(py_file)
        return files

    def extract_class_definitions(self, file_path: Path) -> List[str]:
        """استخراج جميع تعريفات الكلاس من ملف باستخدام AST"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # ✅ تجاهل الكلاس المسموح بتكرارها
                    if node.name not in ALLOWED_DUPLICATE_CLASSES:
                        classes.append(node.name)
            return classes
        except Exception as e:
            print(f"{YELLOW}⚠️{RESET} Failed to parse {file_path}: {e}")
            return []

    def compute_file_hash(self, file_path: Path) -> str:
        """
        ✅ تحسين 2: AST-based normalization بدلاً من regex
        يتجنب مشاكل multiline strings و docstrings
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            # استخدام tokenize لإزالة التعليقات بشكل آمن
            code = content.decode("utf-8")
            tokens = tokenize.generate_tokens(io.StringIO(code).readline)

            normalized_tokens = []
            for tok in tokens:
                # تجاهل التعليقات فقط
                if tok.type != tokenize.COMMENT:
                    normalized_tokens.append(tok.string)

            normalized = " ".join(normalized_tokens)
            normalized = " ".join(normalized.split())  # تطبيع المسافات

            return hashlib.sha256(normalized.encode()).hexdigest()
        except Exception as e:
            print(f"{YELLOW}⚠️{RESET} Hash computation failed for {file_path}: {e}")
            return ""

    def extract_imports(self, file_path: Path) -> List[ImportInfo]:
        """
        ✅ تحسين 3: تتبع دقيق للاستيرادات مع alias و module
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(
                                ImportInfo(
                                    file=file_path,
                                    module=node.module,
                                    name=alias.name,
                                    alias=alias.asname,
                                )
                            )
            return imports
        except Exception as _:
            return []

    def run_full_scan(self):
        """تشغيل المسح الشامل"""
        print("=" * 80)
        print(f"{BLUE}🔍 مسح شامل للكشف عن التكرارات المعمارية — v3.0{RESET}")
        print("=" * 80)

        files = self.scan_all_python_files()
        self.scanned_files_count = len(files)
        print(f"\n📁 جاري فحص {self.scanned_files_count} ملف Python...")

        # 1. جمع تعريفات الكلاس
        for file_path in files:
            classes = self.extract_class_definitions(file_path)
            for cls_name in classes:
                self.class_definitions[cls_name].append(file_path)

            # 2. حساب hash للملف
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                self.file_hashes[file_hash].append(file_path)

            # 3. جمع الاستيرادات
            imports = self.extract_imports(file_path)
            for imp in imports:
                self.import_map[imp.name].append(imp)

        # ✅ تحليل النتائج - تخزين النتائج كمتغيرات حالة (لتجنب التكرار)
        self.critical_class_violations = self.report_duplicate_classes()
        self.report_duplicate_files()
        self.critical_import_violations = self.report_import_conflicts()
        self.architectural_violations = self.report_architecture_violations()

    def report_duplicate_classes(self):
        """تقرير الكلاس مكررة التعريف — مع فلترة ذكية"""
        print(f"\n{BLUE}📌 1. كشف تعريفات الكلاس المكررة:{RESET}")
        print("-" * 80)

        duplicates_found = False
        critical_violations_found = False
        all_critical = CRITICAL_DOMAIN_ENTITIES | CRITICAL_APPLICATION_DTOS
        
        for cls_name, files in self.class_definitions.items():
            if cls_name in ALLOWED_DUPLICATE_CLASSES:
                continue

            if len(files) > 1:
                duplicates_found = True
                print(f"\n{RED}❌ {cls_name}:{RESET}")
                for file_path in files:
                    rel_path = file_path.relative_to(self.root_dir)
                    layer = self._identify_layer(rel_path)
                    print(f"   - {rel_path} [{layer}]")
                
                # ✅ التصحيح: استخدام الثابت الصحيح
                if cls_name in all_critical:
                    print(f"   {RED}🔴 حرج: {cls_name} يجب أن يكون في domain فقط{RESET}")
                    critical_violations_found = True
                else:
                    print(f"   {YELLOW}⚠️ تحذير: مراجعة التكرار{RESET}")

        if not duplicates_found:
            print(f"{GREEN}✅ لا توجد تعريفات كلاس مكررة حرجة{RESET}")
        
        return critical_violations_found

    def report_duplicate_files(self):
        """تقرير الملفات المكررة نصياً"""
        print(f"\n{BLUE}📌 2. كشف الملفات المكررة نصياً:{RESET}")
        print("-" * 80)

        duplicates_found = False
        for file_hash, files in self.file_hashes.items():
            # Only report if there are actual duplicates and a valid hash
            if len(files) > 1 and file_hash and file_hash != "":
                duplicates_found = True
                print(f"\n{RED}❌ ملفات متطابقة نصياً:{RESET}")
                for file_path in files:
                    print(f"   - {file_path.relative_to(self.root_dir)}")
        
        # This return value is not currently used by the caller, but good for future
        if not duplicates_found:
            print(f"{GREEN}✅ لا توجد ملفات مكررة نصياً{RESET}")

    def report_import_conflicts(self):
        """تقرير تعارضات الاستيراد بدقة عالية"""
        print(f"\n{BLUE}📌 3. كشف تعارضات الاستيراد:{RESET}")
        print("-" * 80)

        conflicts_found = False
        critical_import_conflicts = False
        all_critical = CRITICAL_DOMAIN_ENTITIES | CRITICAL_APPLICATION_DTOS
        
        # ✅ التصحيح: استخدام all_critical بدلاً من الثابت القديم
        for entity in all_critical:
            if entity in self.import_map:
                imports = self.import_map[entity]
                sources = set(imp.module for imp in imports)

                if len(sources) > 1:
                    critical_import_conflicts = True
                    conflicts_found = True
                    print(f"\n{RED}❌ {entity} يُستورد من مصادر متعددة:{RESET}")
                    for source in sources:
                        files_using = [
                            str(imp.file.relative_to(self.root_dir))
                            for imp in imports
                            if imp.module == source
                        ]
                        print(f"   - {source}")
                        for f in files_using[:3]:
                            print(f"     * {f}")

                    domain_source = [s for s in sources if "domain" in s]
                    if domain_source:
                        print(f"   {GREEN}✅ الحل: توحيد الاستيراد من {domain_source[0]}{RESET}")
        
        if not conflicts_found:
            print(f"{GREEN}✅ لا توجد تعارضات استيراد للكيانات الحرجة{RESET}")
        
        return critical_import_conflicts

    def report_architecture_violations(self):
        """تقرير انتهاكات الطبقات المعمارية"""
        violations_found = False
        print(f"\n{BLUE}📌 4. كشف انتهاكات الطبقات المعمارية:{RESET}")
        print("-" * 80)

        violations = []

        all_critical = {**{k: "domain/" for k in CRITICAL_DOMAIN_ENTITIES}, 
                        **{k: "application/dtos/" for k in CRITICAL_APPLICATION_DTOS}}

        for cls_name, files in self.class_definitions.items():
            for file_path in files:
                rel_path = str(file_path.relative_to(self.root_dir))

                # قاعدة: الكيانات والـ DTOs يجب أن تلتزم بمواقعها الصحيحة
                if cls_name in all_critical:
                    expected_path = all_critical[cls_name]
                    if expected_path not in rel_path.replace("\\", "/"):
                        violations.append({
                            "entity": cls_name,
                            "file": rel_path,
                            "rule": f"Entity/DTO must be in {expected_path}",
                        })
                        violations_found = True

                # قاعدة: Infrastructure لا يجب أن يكيّن Domain Entities
                if "infrastructure/" in rel_path or "infrastructure\\" in rel_path:
                    if cls_name in CRITICAL_DOMAIN_ENTITIES:
                        # استثناء: alias مع تحذير deprecation
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "DeprecationWarning" not in content:
                                violations.append({
                                    "entity": cls_name,
                                    "file": rel_path,
                                    "rule": "Infrastructure cannot define domain entities",
                                })
                                violations_found = True

        if violations:
            for v in violations:
                print(f"\n{RED}❌ انتهاك معماري:{RESET}")
                print(f"   الكيان: {v['entity']}")
                print(f"   الملف: {v['file']}")
                print(f"   القاعدة: {v['rule']}")
        else:
            print(f"{GREEN}✅ لا توجد انتهاكات معمارية{RESET}")
        
        return violations_found

    def _identify_layer(self, rel_path: Path) -> str:
        """تحديد الطبقة المعمارية للملف"""
        path_str = str(rel_path)
        if "domain/" in path_str or "domain\\" in path_str:
            return "DOMAIN"
        elif "application/" in path_str or "application\\" in path_str:
            return "APPLICATION"
        elif "infrastructure/" in path_str or "infrastructure\\" in path_str:
            return "INFRASTRUCTURE"
        elif "presentation/" in path_str or "presentation\\" in path_str:
            return "PRESENTATION"
        else:
            return "UNKNOWN"

    def generate_summary(self):
        """توليد ملخص نهائي"""
        print("\n" + "=" * 80)
        print(f"{BLUE}📊 ملخص المسح:{RESET}")
        print("=" * 80)

        # ✅ استخدام النتائج المخزنة (لا نعيد استدعاء دوال التقرير)
        critical_class_violations = getattr(self, 'critical_class_violations', False)
        critical_import_violations = getattr(self, 'critical_import_violations', False)
        architectural_violations = getattr(self, 'architectural_violations', False)

        total_classes = len(self.class_definitions)
        duplicate_class_names_count = sum(
            1 for cls_name, files in self.class_definitions.items()
            if len(files) > 1 and cls_name not in ALLOWED_DUPLICATE_CLASSES
        )
        
        duplicate_file_content_count = sum(
            1 for file_hash, files in self.file_hashes.items()
            if len(files) > 1 and file_hash != ""
        )
        
        total_files_scanned = getattr(self, 'scanned_files_count', 0)

        print(f"إجمالي الكلاس المكتشفة: {total_classes}")
        print(f"الكلاس المكررة (بعد الفلترة): {duplicate_class_names_count}")
        print(f"إجمالي الملفات المفحوصة: {total_files_scanned}")
        print(f"الملفات المكررة نصياً: {duplicate_file_content_count}")

        # ✅ التصحيح: استخدام المتغيرات الصحيحة
        if duplicate_class_names_count == 0 and duplicate_file_content_count == 0:
            print(f"\n{GREEN}✅ المشروع نظيف معمارياً - لا توجد تكرارات حرجة{RESET}")
        else:
            print(f"\n{RED}⚠️ توجد {duplicate_class_names_count} كلاس مكررة و {duplicate_file_content_count} ملفات مكررة{RESET}")

        overall_success = not (critical_class_violations or critical_import_violations or 
                            architectural_violations or duplicate_class_names_count > 0 or 
                            duplicate_file_content_count > 0)
        return overall_success


def main():
    import sys

    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = DuplicateDetector(root_dir)
    detector.run_full_scan() # This now calls the reporting methods internally
    
    if not detector.generate_summary():
        sys.exit(1) # Exit with error code if any critical issues found



if __name__ == "__main__":
    main() 