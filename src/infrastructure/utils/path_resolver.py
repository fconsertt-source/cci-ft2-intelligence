from pathlib import Path

def get_project_root() -> Path:
    """
    يحدد جذر المشروع بناءً على موقع هذا الملف.
    
    الهيكل:
    project_root/
    ├── src/
    │   └── infrastructure/
    │       └── utils/
    │           └── path_resolver.py  ← هذا الملف
    ├── assets/
    └── tests/
    
    لذا نحتاج 4 مستويات للأعلى للوصول من utils إلى project_root
    """
    return Path(__file__).resolve().parent.parent.parent.parent  # ✅ 4 مستويات وليس 3

def get_assets_dir() -> Path:
    """يُرجع مسار مجلد assets بغض النظر عن مكان تشغيل السكربت"""
    return get_project_root() / "assets"

def get_verifiers_dir() -> Path:
    """يُرجع مسار مجلد أدوات التحقق"""
    return get_assets_dir() / "verifiers"

def get_berlinger_verifier_path(jar_filename: str) -> Path:
    """
    يُرجع المسار الكامل لملف JAR الخاص بـ Berlinger.
    """
    return get_verifiers_dir() / "berlinger" / jar_filename

def get_runtime_dir() -> Path:
    """يُرجع مسار مجلد بيئات التشغيل (JRE/JDK)"""
    return get_assets_dir() / "runtime"

def get_runtime_manifest_path() -> Path:
    """يُرجع مسار ملف بيان البيئة الأمني"""
    return get_runtime_dir() / "runtime_manifest.json"