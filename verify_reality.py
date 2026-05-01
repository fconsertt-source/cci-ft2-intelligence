#!/usr/bin/env python3
"""
مرساة الواقع (The Reality Anchor): تحقق ساكن وآمن من الموديولات دون المخاطرة بتنفيذها.
"""
import sys
import os
import importlib.util
import ast

# 1. قائمة الملفات
files_to_check =[
    'src.domain.validators.ft2_entry_validator',
    'src.application.services.center_impact_service',
    'src.infrastructure.validation.default_validator',
]

MAX_FILE_SIZE = 1024 * 1024  # 1 ميجابايت (حماية ضد Memory Exhaustion DoS)

def safe_module_exists(module_name):
    """
    التحقق من الوجود الساكن: نكتفي بالبحث عن المواصفات (Spec) دون التنفيذ.
    هذا يمنع هجوم Dynamic Dependency Injection.
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except Exception as e:
        print(f"خطأ في مسار {module_name}: {e}")
        return False

def check_ft2_validator_ast():
    """
    التشريح الساكن باستخدام شجرة بناء الجملة (AST) لاكتشاف الاستيرادات الخبيثة.
    """
    raw_path = '/home/amer11974/projects/cci-ft2-intelligence-clean/src/domain/validators/ft2_entry_validator.py'
    
    # حماية ضد هجمات الروابط الوهمية (Symlink Attacks)
    file_path = os.path.realpath(raw_path)
    
    if not os.path.isfile(file_path):
        print(f"الملف {file_path} غير موجود أو ليس ملفاً حقيقياً.")
        return False
        
    # حماية ضد استنفاد الذاكرة (Memory Exhaustion)
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        print("الملف يتجاوز الحجم المسموح به (احتمال هجوم DoS).")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"فشل قراءة الملف: {e}")
        return False

    # التحليل الدلالي (Semantic Analysis) عبر AST بدلاً من البحث النصي الأعمى
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"الملف يحتوي على أخطاء بناء جملة (Syntax Error): {e}")
        return False

    # فحص جميع عقد الشجرة بحثاً عن استيراد صريح أو ضمني
    for node in ast.walk(tree):
        # التقاط استيراد مباشر: import pydantic
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'pydantic' in alias.name or 'infrastructure' in alias.name:
                    print(f"اكتشاف استيراد ممنوع مباشر: {alias.name}")
                    return False
        
        # التقاط استيراد جزئي: from pydantic import BaseModel
        elif isinstance(node, ast.ImportFrom):
            if node.module and ('pydantic' in node.module or 'infrastructure' in node.module):
                print(f"اكتشاف استيراد ممنوع من موديول: {node.module}")
                return False
                
        # التقاط محاولات الاستيراد الديناميكي: __import__('pydantic')
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == '__import__':
                print("تم اكتشاف محاولة استيراد ديناميكي (Dynamic Import) - مرفوض أمنياً.")
                return False

    return True

if __name__ == "__main__":
    success = True
    
    # 1. التحقق الساكن من وجود الموديولات
    for mod in files_to_check:
        if not safe_module_exists(mod):
            print(f"الموديول مفقود: {mod}")
            success = False
            
    # 2. التحليل الدلالي للملف المستهدف
    if not check_ft2_validator_ast():
        success = False
        
    if not success:
        sys.exit(1)
    
    print("تم التحقق من الواقع بنجاح وبأمان تام.")
    sys.exit(0)
    print("جميع الملفات موجودة وصحيحة")