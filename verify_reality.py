#!/usr/bin/env python3
"""
فخ الوجود الوهمي: يتحقق من وجود الملفات المذكورة في التقارير.
"""
import sys
import os
import importlib.util

# قائمة الملفات المذكورة في التقارير (بناءً على السياق)
files_to_check = [
    'src.domain.validators.ft2_entry_validator',
    'src.application.services.center_impact_service',
    'src.infrastructure.validation.default_validator',
]

def try_import(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            raise ModuleNotFoundError(f"No module named '{module_name}'")
        # محاولة تحميل الموديول
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"فشل استيراد {module_name}: {e}")
        return False

def check_ft2_validator():
    # التحقق من عدم وجود pydantic أو infrastructure في ft2_entry_validator.py
    file_path = '/home/amer11974/projects/cci-ft2-intelligence-clean/src/domain/validators/ft2_entry_validator.py'
    if not os.path.exists(file_path):
        print(f"الملف {file_path} غير موجود")
        return False
    with open(file_path, 'r') as f:
        content = f.read()
    if 'pydantic' in content or 'infrastructure' in content:
        print("يحتوي على استيراد ممنوع")
        return False
    return True

if __name__ == "__main__":
    success = True
    for mod in files_to_check:
        if not try_import(mod):
            success = False
    if not check_ft2_validator():
        success = False
    if not success:
        sys.exit(1)
    print("جميع الملفات موجودة وصحيحة")