# scripts/debug_ft2.py
import os
import sys
import csv

def clean_bad_files():
    """حذف الملفات الفارغة أو التالفة من data/input_ft2"""
    target_dir = "data/input_ft2"
    if not os.path.exists(target_dir):
        print(f"⚠️ المجلد {target_dir} غير موجود.")
        return

    print(f"\n{'='*50}")
    print(f"🧹 تنظيف الملفات التالفة في {target_dir}")
    print(f"{'='*50}")
    
    removed_count = 0
    for file in os.listdir(target_dir):
        if not file.endswith('.txt'):
            continue
            
        filepath = os.path.join(target_dir, file)
        try:
            should_remove = False
            reason = ""
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # معايير الملف التالف
            if not content.strip():
                should_remove = True
                reason = "فارغ تماماً"
            elif "Hist:" in content and "Date:" not in content:
                should_remove = True
                reason = "لا يحتوي على بيانات (فشل التحويل)"
            
            if should_remove:
                os.remove(filepath)
                print(f"🗑️ تم حذف: {file} ({reason})")
                removed_count += 1
                
        except Exception as e:
            print(f"❌ خطأ في فحص {file}: {e}")
            
    if removed_count == 0:
        print("✨ لم يتم العثور على ملفات تالفة.")
    else:
        print(f"✅ تم تنظيف {removed_count} ملف.")

def debug_raw_files():
    """فحص الملفات الخام (TSV/CSV) في data/input_raw"""
    input_dir = "data/input_raw"
    
    if not os.path.exists(input_dir):
        print(f"⚠️ المجلد {input_dir} غير موجود.")
        return

    print(f"\n{'#'*50}")
    print(f"فحص الملفات الخام في: {input_dir}")
    print(f"{'#'*50}")

    files = [f for f in os.listdir(input_dir) if f.endswith(('.tsv', '.csv'))]
    if not files:
        print("لا توجد ملفات .tsv أو .csv.")
        print("💡 تلميح: جرب إنشاء بيانات اختبار أولاً باستخدام: python -m scripts.run_ft2_pipeline --generate-data")
        return

    for file in files:
        filepath = os.path.join(input_dir, file)
        print(f"\n📄 الملف: {file}")
        print("-" * 30)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            if not content.strip():
                print("⚠️  الملف فارغ تماماً!")
                continue

            lines = content.splitlines()
            print(f"📊 عدد الأسطر: {len(lines)}")
            
            print("📝 أول 5 أسطر:")
            for i, line in enumerate(lines[:5]):
                # طباعة السطر كما هو مع إظهار الأحرف غير المرئية (مثل \t)
                print(f"  {i+1}: {repr(line)}")
                
        except Exception as e:
            print(f"❌ خطأ في قراءة الملف: {e}")

def debug_ft2_files():
    """تصحيح مشاكل ملفات FT2"""
    input_dir = "data/input_ft2"
    
    for file in os.listdir(input_dir):
        filepath = os.path.join(input_dir, file)
        
        if file.endswith('.txt'):
            print(f"\n{'='*50}")
            print(f"فحص الملف: {file}")
            print(f"{'='*50}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                print("⚠️  الملف فارغ تماماً!")
            else:
                lines = content.split('\n')
                print(f"عدد الأسطر: {len(lines)}")
                print(f"أول 5 أسطر:")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}: {line[:100]}{'...' if len(line)>100 else ''}")
                
                # البحث عن كلمات مفتاحية
                keywords = ['Hist:', 'Date:', 'Min T:', 'Serial:']
                for kw in keywords:
                    if kw in content:
                        print(f"✅ وجد: {kw}")
                    else:
                        print(f"❌ لم يجد: {kw}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_bad_files()
    else:
        debug_raw_files()
        debug_ft2_files()
        print("\n💡 تلميح: لتنظيف الملفات التالفة تلقائياً، شغّل: python scripts/debug_ft2.py --clean")