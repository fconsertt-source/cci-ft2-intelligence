#!/usr/bin/env python3
"""
CCI-FT2 Remediation Tool: DTO Migration
ينقل الـ DTOs من Domain إلى Application وفقاً للخطة v1.3.
"""
import shutil
import os
from pathlib import Path

DOMAIN_DTOS = Path("src/domain/dtos")
APP_DTOS = Path("src/application/dtos")

def migrate():
    print("🚀 بدء هجرة الـ DTOs من Domain إلى Application...")
    
    if not DOMAIN_DTOS.exists():
        print("✅ لا يوجد مجلد dtos في domain. قد تمت الهجرة مسبقاً.")
        return

    APP_DTOS.mkdir(parents=True, exist_ok=True)
    
    conflicts = []
    migrated = []

    for dto_file in DOMAIN_DTOS.glob("*.py"):
        if dto_file.name == "__init__.py":
            continue

        target = APP_DTOS / dto_file.name

        if target.exists():
            # تعارض — يحتاج مراجعة يدوية
            conflicts.append({
                "file": dto_file.name,
                "domain_size": dto_file.stat().st_size,
                "app_size": target.stat().st_size
            })
        else:
            # نقل آمن
            shutil.copy2(dto_file, target)
            migrated.append(dto_file.name)

    # تقرير
    print(f"\n✅ تم نقل {len(migrated)} ملف:")
    for f in migrated:
        print(f"  → {f}")

    if conflicts:
        print(f"\n⚠️ {len(conflicts)} ملف يحتاج مراجعة يدوية (موجود مسبقاً في Application):")
        for c in conflicts:
            print(f"  - {c['file']}: Domain ({c['domain_size']} bytes) vs App ({c['app_size']} bytes)")
        return False

    print("\n🧹 تنظيف المجلد القديم...")
    # ملاحظة: يفضل حذف المجلد يدوياً بعد التأكد من الاستيرادات
    # shutil.rmtree(DOMAIN_DTOS) 
    
    return True

if __name__ == "__main__":
    success = migrate()
    if not success:
        exit(1)